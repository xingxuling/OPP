"""OPP Bridge Compiler（OPP 桥编译器）orchestrator。"""
from __future__ import annotations
import json
from pathlib import Path
from ..integrity import content_root
from ..validation import validate_envelope
from .scanner import scan_repository
from .mapper import evidence_envelope,artifact_envelope,capability_envelope,handshake_offer,DEFAULT_ISSUED_AT


def compile_bridge(source: str|Path, *, output_dir: str|Path|None=None, source_id: str|None=None, profile: str='auto', issued_at: str=DEFAULT_ISSUED_AT, max_findings: int=5000) -> dict:
    report=scan_repository(source,source_id=source_id,profile=profile)
    issuer="taowind.opp.bridge-compiler.v0.1"
    evidence=[]; artifacts=[]; capabilities=[]
    selected=report.findings[:max_findings]
    for f in selected:
        rep=evidence_envelope(report,f,issuer,issued_at=issued_at); evidence.append(rep)
        rap=artifact_envelope(report,f,issuer,rep['id'],issued_at=issued_at); artifacts.append(rap)
        rcp=capability_envelope(report,f,issuer,rep['id'],issued_at=issued_at); capabilities.append(rcp)
    offer=handshake_offer(report,issuer,[x['payload']['capabilityId'] for x in capabilities],[f.native_id for f in selected if f.kind in {'protocol','contract','interface','bridge'}],issued_at=issued_at)
    all_env=[*evidence,*artifacts,*capabilities,offer]
    validation={env['id']:[i.__dict__ for i in validate_envelope(env)] for env in all_env}
    invalid={k:v for k,v in validation.items() if v}
    manifest_core={"format":"taowind.opp.bridge-manifest.v0.1","version":"0.1.0-candidate.1","sourceId":report.source_id,"profile":report.profile,"scanRoot":content_root(report.to_dict()),"findingCount":len(report.findings),"emittedFindingCount":len(selected),"truncated":report.truncated or len(report.findings)>len(selected),"artifacts":{"scan":"scan.json","evidenceCount":len(evidence),"artifactCount":len(artifacts),"capabilityCount":len(capabilities),"handshake":"handshake.json"},"validation":{"valid":not invalid,"invalidEnvelopeCount":len(invalid)},"authority":{"canonicalPromotionPerformed":False,"sourceAuthorityInherited":False},"boundary":"Bridge output is candidate-only. Static discovery does not establish native runtime support or real-world truth / 桥输出仅为候选；静态发现不证明原生运行支持或现实真实性。"}
    manifest={**manifest_core,"manifestRoot":content_root(manifest_core)}
    result={"manifest":manifest,"scan":report.to_dict(),"evidence":evidence,"artifacts":artifacts,"capabilities":capabilities,"handshake":offer,"validation":validation}
    if output_dir is not None: write_bridge_bundle(result,output_dir)
    return result


def write_bridge_bundle(result: dict, output_dir: str|Path) -> Path:
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    def dump(name,obj): (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding='utf-8')
    dump('manifest.json',result['manifest']); dump('scan.json',result['scan']); dump('handshake.json',result['handshake']); dump('validation.json',result['validation'])
    for folder,key in [('evidence','evidence'),('artifacts','artifacts'),('capabilities','capabilities')]:
        d=out/folder; d.mkdir(exist_ok=True)
        for obj in result[key]: dump(str(Path(folder)/f"{obj['id']}.json"),obj)
    return out
