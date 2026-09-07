from __future__ import annotations
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from opp.bridge import SemanticPort, synthesize_bridge
from opp.runtime import run_invocation, InvocationError, run_interop, InteropError
from opp.registry import repository_root

ROOT=repository_root()
FIX=ROOT/'examples'/'native-fixtures'

def inv(entry, spec_id='test', timeout=3000, max_output=262144, adapter='python-function'):
    return {
        'format':'taowind.opp.invocation-spec.v0.1','version':'0.3.0-candidate.1','specId':spec_id,'adapterKind':adapter,
        'sourceRoot':str(ROOT),'entrypoint':entry,'callingConvention':'kwargs','timeoutMs':timeout,'maxOutputBytes':max_output,
        'cwdPolicy':'ephemeral','environmentPolicy':'sanitized','authorityRequired':[],'status':'candidate'
    }

def structural_plan():
    p=SemanticPort('producer.user','user','output',{'type':'object','properties':{'user_name':{'type':'string'},'age':{'type':'integer'},'debug':{'type':'boolean'}},'required':['user_name','age','debug'],'additionalProperties':False},'json',('user',),True,None,.99)
    c=SemanticPort('consumer.user','user','input',{'type':'object','properties':{'username':{'type':'string'},'age':{'type':'number'},'locale':{'type':'string','default':'zh-HK'}},'required':['username','age','locale'],'additionalProperties':False},'json',('user',),True,None,.99)
    return synthesize_bridge(p,c,allow_lossy=True)

class NativeInteropTests(unittest.TestCase):
    def test_invocation_requires_explicit_consent(self):
        with self.assertRaises(InvocationError):
            run_invocation(inv('examples/native-fixtures/producer.py:produce_user'),{'user_name':'Ada','age':20})

    def test_invocation_spec_format_fails_closed(self):
        spec=inv('examples/native-fixtures/producer.py:produce_user')
        spec['format']='taowind.opp.invocation-spec.v9'
        with self.assertRaises(InvocationError):
            run_invocation(spec,{'user_name':'Ada','age':20},allow_execution=True)

    def test_invocation_spec_id_required(self):
        spec=inv('examples/native-fixtures/producer.py:produce_user')
        spec['specId']=''
        with self.assertRaises(InvocationError):
            run_invocation(spec,{'user_name':'Ada','age':20},allow_execution=True)

    def test_python_invocation_pass_and_receipt_schema(self):
        result=run_invocation(inv('examples/native-fixtures/producer.py:produce_user','producer'),{'user_name':'Ada','age':20},allow_execution=True)
        self.assertEqual('PASS',result['receipt']['status'])
        self.assertEqual({'user_name':'Ada','age':20,'debug':True},result['result'])
        self.assertIn('producer-called',result['receipt']['targetStdout'])
        schema=json.loads((ROOT/'schemas'/'invocation-receipt.schema.json').read_text(encoding='utf-8'))
        self.assertEqual([],list(Draft202012Validator(schema).iter_errors(result['receipt'])))

    def test_path_escape_rejected(self):
        spec=inv('../escape.py:run')
        with self.assertRaises(InvocationError): run_invocation(spec,{},allow_execution=True)

    def test_symlink_entrypoint_rejected(self):
        if not hasattr(os,'symlink'): self.skipTest('symlink unavailable')
        link=ROOT/'examples'/'native-fixtures'/'producer-link.py'
        try:
            if link.exists() or link.is_symlink(): link.unlink()
            os.symlink(FIX/'producer.py',link)
            with self.assertRaises(InvocationError): run_invocation(inv('examples/native-fixtures/producer-link.py:produce_user'),{'user_name':'Ada','age':20},allow_execution=True)
        finally:
            if link.exists() or link.is_symlink(): link.unlink()

    def test_shell_adapter_rejected(self):
        with self.assertRaises(InvocationError): run_invocation(inv('examples/native-fixtures/producer.py:produce_user',adapter='shell'),{},allow_execution=True)

    def test_timeout_fails_closed(self):
        result=run_invocation(inv('examples/native-fixtures/sleepy.py:sleepy','sleepy',timeout=100),{'value':1},allow_execution=True)
        self.assertEqual('FAIL',result['receipt']['status']); self.assertTrue(result['receipt']['timedOut']); self.assertEqual('INVOCATION_TIMEOUT',result['receipt']['error'])

    def test_non_json_result_fails(self):
        result=run_invocation(inv('examples/native-fixtures/nonjson.py:nonjson','nonjson'),{'value':3},allow_execution=True)
        self.assertEqual('FAIL',result['receipt']['status']); self.assertIsNone(result['result'])

    def test_output_overflow_fails_closed(self):
        result=run_invocation(inv('examples/native-fixtures/loud.py:loud','loud',max_output=1024),{'value':3},allow_execution=True)
        self.assertEqual('FAIL',result['receipt']['status']); self.assertEqual('OUTPUT_LIMIT_EXCEEDED',result['receipt']['error'])

    def test_deterministic_receipt_root_excludes_timing_noise(self):
        spec=inv('examples/native-fixtures/producer.py:produce_user','deterministic')
        a=run_invocation(spec,{'user_name':'Ada','age':20},allow_execution=True)
        b=run_invocation(spec,{'user_name':'Ada','age':20},allow_execution=True)
        self.assertEqual(a['receipt']['receiptRoot'],b['receipt']['receiptRoot'])

    def test_end_to_end_structural_interop(self):
        plan=structural_plan(); self.assertEqual('candidate',plan['status'])
        run_spec={'format':'taowind.opp.interop-run.v0.1','version':'0.3.0-candidate.1','runId':'fixture-e2e','producer':inv('examples/native-fixtures/producer.py:produce_user','producer'),'bridgePlan':plan,'consumer':inv('examples/native-fixtures/consumer.py:consume_user','consumer'),'status':'candidate'}
        result=run_interop(run_spec,{'user_name':'Ada','age':20},allow_execution=True)
        self.assertEqual('PASS',result['receipt']['status'])
        self.assertEqual({'username':'Ada','age':20,'locale':'zh-HK'},result['transformed'])
        self.assertEqual({'accepted':True,'username':'Ada','age':20,'locale':'zh-HK'},result['result'])
        schema=json.loads((ROOT/'schemas'/'interop-receipt.schema.json').read_text(encoding='utf-8'))
        self.assertEqual([],list(Draft202012Validator(schema).iter_errors(result['receipt'])))

    def test_rejected_bridge_not_executed(self):
        plan=structural_plan(); plan={**plan,'status':'rejected'}
        run_spec={'format':'taowind.opp.interop-run.v0.1','version':'0.3.0-candidate.1','runId':'rejected','producer':inv('examples/native-fixtures/producer.py:produce_user'),'bridgePlan':plan,'consumer':inv('examples/native-fixtures/consumer.py:consume_user'),'status':'candidate'}
        with self.assertRaises(InteropError): run_interop(run_spec,{'user_name':'Ada','age':20},allow_execution=True)

    def test_cli_interop_requires_gate_and_passes_with_gate(self):
        plan=structural_plan()
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); runp=td/'run.json'; inp=td/'input.json'; out=td/'out.json'
            runp.write_text(json.dumps({'format':'taowind.opp.interop-run.v0.1','version':'0.3.0-candidate.1','runId':'cli-e2e','producer':inv('examples/native-fixtures/producer.py:produce_user'),'bridgePlan':plan,'consumer':inv('examples/native-fixtures/consumer.py:consume_user'),'status':'candidate'}),encoding='utf-8')
            inp.write_text(json.dumps({'user_name':'Ada','age':20}),encoding='utf-8')
            p=subprocess.run([sys.executable,'-m','opp','interop','run',str(runp),str(inp),'--out',str(out)],capture_output=True,text=True,cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'src')})
            self.assertNotEqual(0,p.returncode)
            p=subprocess.run([sys.executable,'-m','opp','interop','run',str(runp),str(inp),'--allow-execution','--out',str(out)],capture_output=True,text=True,cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'src')})
            self.assertEqual(0,p.returncode,p.stderr+p.stdout)
            data=json.loads(out.read_text(encoding='utf-8')); self.assertEqual('PASS',data['receipt']['status'])

if __name__=='__main__': unittest.main()
