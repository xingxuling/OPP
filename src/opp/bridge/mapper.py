"""Map static findings into existing OPP envelopes（映射到既有 OPP 协议）。"""
from __future__ import annotations
import hashlib
from typing import Iterable
from ..integrity import seal_envelope
from .model import PrimitiveFinding, ScanReport

DEFAULT_ISSUED_AT="1970-01-01T00:00:00Z"  # reproducible-build time, not a source timestamp

def _slug_hash(*parts: str)->str:
    return hashlib.sha256('\0'.join(parts).encode('utf-8')).hexdigest()[:24]

def _env(protocol,kind,id_,issuer,payload,*,issued_at=DEFAULT_ISSUED_AT,constraints=(),evidence_refs=(),extensions=None):
    return seal_envelope({"format":"taowind.opp.reality-envelope.v0.1","protocol":protocol,"version":"0.1.0-candidate.1","kind":kind,"id":id_,"status":"candidate","issuedAt":issued_at,"issuer":{"id":issuer,"type":"service","displayName":"OPP Bridge Compiler / OPP 桥编译器"},"payload":payload,"constraints":list(constraints),"evidenceRefs":list(evidence_refs),"extensions":extensions or {}})

def evidence_envelope(report: ScanReport, f: PrimitiveFinding, issuer: str, *, issued_at=DEFAULT_ISSUED_AT):
    sid=f"source-{_slug_hash(report.source_id,f.source.path,f.source.digest)}"
    bid=f"evidence-{_slug_hash(f.finding_id,f.source.digest)}"
    return _env("opp.rep.v0.1","evidence",bid,issuer,{"bundleId":bid,"claims":[{"claimId":f"claim-{f.finding_id}","statement":f"Static scan found candidate {f.kind} identifier {f.native_id} in {f.source.path}","status":"partially-supported","sourceRefs":[sid]}],"sources":[{"sourceId":sid,"sourceType":"file","locator":f.source.path,"digest":f.source.digest}],"method":f"static-{f.source.extractor}","confidence":round(f.confidence,4),"independence":"derived","negativeEvidence":[],"reproduction":{"available":True,"instructions":["Run opp bridge scan against the same source snapshot / 对同一源码快照运行 opp bridge scan"],"environment":"static reader; discovered code is not executed"},"boundary":"Lexical/static discovery supports the existence of this candidate declaration only; it does not prove runtime support, truth, ownership, interoperability, or authority / 静态发现只支持‘候选声明存在’，不证明运行支持、真实性、所有权、互操作性或权限。","authority":"none"},issued_at=issued_at)

def artifact_envelope(report: ScanReport, f: PrimitiveFinding, issuer: str, evidence_id: str, *, issued_at=DEFAULT_ISSUED_AT):
    aid=f"artifact-{_slug_hash(f.finding_id,f.native_id)}"
    return _env("opp.rap.v0.1","protocol",aid,issuer,{"artifactId":aid,"artifactType":f"discovered-{f.kind}","purpose":f"Represent a statically discovered {f.kind} candidate without semantic promotion / 表示静态发现的 {f.kind} 候选，不做语义晋级","version":"0.1.0-candidate.1","contentRef":f.source.path,"contentRoot":f.source.digest,"dependencies":[],"provenance":[{"source":f.source.path,"relation":"static-discovery","digest":f.source.digest}],"constraints":["candidate-only","no-source-execution","no-authority-promotion"],"acceptance":[{"gate":"static-discovery","status":"pass","evidenceRef":evidence_id},{"gate":"runtime-support","status":"unverified"}],"lifecycle":"candidate","executableSemantics":None,"interfaces":[f.native_id] if f.kind in {'protocol','contract','interface','bridge'} else [],"evidenceRefs":[evidence_id]},issued_at=issued_at)

def capability_envelope(report: ScanReport, f: PrimitiveFinding, issuer: str, evidence_id: str, *, issued_at=DEFAULT_ISSUED_AT):
    cid=f"bridge.describe.{f.kind}.{_slug_hash(f.native_id)[:12]}"
    eid=f"capability-{_slug_hash(f.finding_id,cid)}"
    return _env("opp.rcp.v0.1","capability",eid,issuer,{"capabilityId":cid,"name":f"Describe discovered {f.kind}: {f.name}","domain":"bridge.discovery","operation":f"describe.{f.kind}","inputModalities":["repository-snapshot"],"outputModalities":["opp-candidate-envelope"],"determinism":"deterministic","statefulness":"stateless","streaming":False,"authorityRequired":[],"sideEffects":[],"reversibility":"reversible","availability":"candidate-only","rights":{"sourceAuthorityInherited":False,"canonicalPromotionPerformed":False},"evidence":[evidence_id],"claimBoundary":"This is Bridge Compiler capability to describe a declaration; it is not a claim that the scanned system can execute the declaration / 这是桥编译器描述声明的能力，不代表被扫描系统能执行该声明。"},issued_at=issued_at)

def handshake_offer(report: ScanReport, issuer: str, capability_ids: Iterable[str], native_ids: Iterable[str], *, issued_at=DEFAULT_ISSUED_AT):
    hid=f"handshake-{_slug_hash(report.source_id,report.profile)}"
    return _env("opp.chp.v0.1","protocol",hid,issuer,{"phase":"offer","identity":{"id":f"bridge:{report.source_id}","civilizationType":"service","displayName":f"OPP bridge for {report.source_id}"},"supportedProtocols":["opp.chp.v0.1","opp.rcp.v0.1","opp.rap.v0.1","opp.rep.v0.1"],"capabilities":sorted(set(capability_ids)),"authorityScopes":[],"evidencePolicy":{"minimumConfidence":0.0,"acceptDerivedEvidence":True,"requiredProtocols":["opp.rep.v0.1"]},"extensions":{"profile":report.profile,"nativeProtocolCandidates":sorted(set(native_ids)),"boundary":"Generated bridge offer; no source-system authority is inherited / 生成的桥握手，不继承源系统权限。"}},issued_at=issued_at)
