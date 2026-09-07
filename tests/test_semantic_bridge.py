from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from opp.bridge import (
    SemanticPort, verify_repository_semantics, compare_ports, synthesize_bridge, apply_transform, TransformError, compile_bridge, plan_repository_connection
)
from opp.integrity import content_root
from opp.registry import repository_root
from opp.validation import validate_envelope

ROOT=repository_root(); FIX=ROOT/'examples'/'semantic-fixtures'

def port(pid,name,direction,shape,tags=(),confidence=.95,default=None,required=True):
    return SemanticPort(pid,name,direction,shape,'json',tuple(tags),required,default,confidence)

class SemanticBridgeTests(unittest.TestCase):
    def test_static_python_and_ts_semantics(self):
        report=verify_repository_semantics(FIX,profile='generic')
        names={i.operation for i in report.interfaces}
        self.assertTrue({'produce_user','consume_user','normalizeUser'} <= names)
        consume=next(i for i in report.interfaces if i.operation=='consume_user')
        self.assertEqual({'username','age','locale'},{p.name for p in consume.inputs})
        locale=next(p for p in consume.inputs if p.name=='locale')
        self.assertFalse(locale.required); self.assertEqual('zh-HK',locale.default)
        self.assertEqual({'type':'boolean'},consume.outputs[0].shape)

    def test_semantic_report_schema(self):
        report=verify_repository_semantics(FIX,profile='generic').to_dict()
        schema=json.loads((ROOT/'schemas'/'semantic-verification.schema.json').read_text(encoding='utf-8'))
        self.assertEqual([],list(Draft202012Validator(schema).iter_errors(report)))

    def test_normalized_rename_default_and_projection(self):
        producer=port('p','user','output',{'type':'object','properties':{'user_name':{'type':'string'},'age':{'type':'integer'},'debug':{'type':'boolean'}},'required':['user_name','age','debug'],'additionalProperties':False},('user',))
        consumer=port('c','user','input',{'type':'object','properties':{'username':{'type':'string'},'age':{'type':'number'},'locale':{'type':'string','default':'zh-HK'}},'required':['username','age','locale'],'additionalProperties':False},('user',))
        result=compare_ports(producer,consumer)
        self.assertEqual('lossy',result.classification)
        ops=list(result.operations)
        self.assertIn({'op':'rename','from':'user_name','to':'username'},ops)
        self.assertIn({'op':'inject-default','field':'locale','value':'zh-HK'},ops)
        self.assertTrue(any(x.get('op')=='select' for x in ops))
        rejected=synthesize_bridge(producer,consumer)
        self.assertEqual('rejected',rejected['status'])
        plan=synthesize_bridge(producer,consumer,allow_lossy=True)
        self.assertEqual('candidate',plan['status'])
        out=apply_transform({'user_name':'Ada','age':20,'debug':True},plan['operations'])
        self.assertEqual({'username':'Ada','age':20,'locale':'zh-HK'},out)

    def test_missing_information_refuses(self):
        producer=port('p','x','output',{'type':'object','properties':{'a':{'type':'string'}},'required':['a']})
        consumer=port('c','x','input',{'type':'object','properties':{'a':{'type':'string'},'token':{'type':'string'}},'required':['a','token']})
        result=compare_ports(producer,consumer); self.assertEqual('incompatible',result.classification); self.assertIn('$.token',result.missing_information)
        plan=synthesize_bridge(producer,consumer); self.assertEqual('rejected',plan['status']); self.assertEqual([],plan['operations']); self.assertFalse(plan['safety']['informationInvention'])

    def test_authority_invention_refuses(self):
        p=port('p','x','output',{'type':'string'}); c=port('c','x','input',{'type':'string'})
        result=compare_ports(p,c,producer_authority=['read'],consumer_authority=['write'])
        self.assertEqual('incompatible',result.classification); self.assertEqual(('write',),result.authority_gap)
        plan=synthesize_bridge(p,c,producer_authority=['read'],consumer_authority=['write'])
        self.assertEqual('rejected',plan['status']); self.assertFalse(plan['safety']['authorityInvention'])

    def test_plan_deterministic_and_schema_valid(self):
        p=port('p','x','output',{'type':'integer'},('count',)); c=port('c','x','input',{'type':'number'},('count',))
        a=synthesize_bridge(p,c); b=synthesize_bridge(p,c)
        self.assertEqual(a['planRoot'],b['planRoot'])
        schema=json.loads((ROOT/'schemas'/'auto-bridge-plan.schema.json').read_text(encoding='utf-8'))
        self.assertEqual([],list(Draft202012Validator(schema).iter_errors(a)))
        cschema=json.loads((ROOT/'schemas'/'bridge-compatibility.schema.json').read_text(encoding='utf-8'))
        self.assertEqual([],list(Draft202012Validator(cschema).iter_errors(a['compatibility'])))

    def test_transform_runtime_rejects_arbitrary_code(self):
        with self.assertRaises(TransformError): apply_transform({'x':1},[{'op':'python','code':'import os'}])

    def test_bridge_compile_projects_semantic_capabilities(self):
        result=compile_bridge(FIX,source_id='semantic-fixture',profile='generic')
        self.assertGreaterEqual(result['manifest']['artifacts']['semanticInterfaceCount'],3)
        self.assertGreaterEqual(result['manifest']['artifacts']['semanticCapabilityCount'],3)
        self.assertTrue(result['manifest']['validation']['valid'])
        for env in result['semanticCapabilities']:
            self.assertEqual([],validate_envelope(env))
            self.assertEqual('candidate-only',env['payload']['availability'])
            self.assertFalse(env['payload']['rights']['sourceAuthorityInherited'])


    def test_auto_connect_between_project_shapes(self):
        producer=verify_repository_semantics(FIX,source_id='producer-project',profile='generic')
        # use a consumer-only temporary project so the planner cannot cheat by connecting fixture to itself
        with tempfile.TemporaryDirectory() as td:
            Path(td,'consumer.py').write_text((FIX/'consumer.py').read_text(encoding='utf-8'),encoding='utf-8')
            consumer=verify_repository_semantics(td,source_id='consumer-project',profile='generic')
            result=plan_repository_connection(producer,consumer,max_plans=20)
            self.assertGreater(result['pairsCompared'],0)
            self.assertGreaterEqual(result['acceptedPlanCount'],1)
            plan=next(p for p in result['plans'] if p['consumerInterface']['operation']=='consume_user')
            self.assertEqual('structural',plan['compatibility']['classification'])
            self.assertIn({'op':'rename','from':'user_name','to':'username'},plan['operations'])
            self.assertNotIn('$.locale',plan['compatibility']['missingInformation'])
            schema=json.loads((ROOT/'schemas'/'auto-connect-report.schema.json').read_text(encoding='utf-8'))
            self.assertEqual([],list(Draft202012Validator(schema).iter_errors(result)))

    def test_cli_auto_connect(self):
        with tempfile.TemporaryDirectory() as td:
            consumer_dir=Path(td)/'consumer'; consumer_dir.mkdir()
            (consumer_dir/'consumer.py').write_text((FIX/'consumer.py').read_text(encoding='utf-8'),encoding='utf-8')
            out=Path(td)/'connect.json'
            p=subprocess.run([sys.executable,'-m','opp','semantic','connect',str(FIX),str(consumer_dir),'--producer-profile','generic','--consumer-profile','generic','--out',str(out)],capture_output=True,text=True)
            self.assertEqual(0,p.returncode,p.stderr+p.stdout)
            data=json.loads(out.read_text(encoding='utf-8')); self.assertGreaterEqual(data['acceptedPlanCount'],1)

    def test_cli_semantic_verify(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'semantic.json'
            p=subprocess.run([sys.executable,'-m','opp','semantic','verify',str(FIX),'--profile','generic','--out',str(out)],capture_output=True,text=True)
            self.assertEqual(0,p.returncode,p.stderr+p.stdout); self.assertTrue(out.exists())
            data=json.loads(out.read_text(encoding='utf-8')); self.assertGreaterEqual(data['interfaceCount'],3)

if __name__=='__main__': unittest.main()
