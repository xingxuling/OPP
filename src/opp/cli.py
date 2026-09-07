"""OPP CLI（命令行接口）。"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from .handshake import negotiate_handshake
from .validation import validate_envelope

def load(path: str) -> dict: return json.loads(Path(path).read_text(encoding="utf-8"))

def _bridge_cmd(args) -> int:
    from .bridge import scan_repository, compile_bridge
    if args.bridge_command=="scan":
        result=scan_repository(args.source,source_id=args.source_id,profile=args.profile,max_files=args.max_files,max_total_bytes=args.max_bytes).to_dict()
        text=json.dumps(result,ensure_ascii=False,indent=2)
        if args.out: Path(args.out).write_text(text+"\n",encoding='utf-8')
        print(text); return 0
    result=compile_bridge(args.source,output_dir=args.out,source_id=args.source_id,profile=args.profile,max_findings=args.max_findings)
    print(json.dumps({"status":"PASS" if result['manifest']['validation']['valid'] else "FAIL","状态":"通过" if result['manifest']['validation']['valid'] else "失败","output":str(args.out),"profile":result['manifest']['profile'],"findings":result['manifest']['findingCount'],"emitted":result['manifest']['emittedFindingCount'],"canonicalPromotionPerformed":False,"boundary":result['manifest']['boundary']},ensure_ascii=False,indent=2))
    return 0 if result['manifest']['validation']['valid'] else 2

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description="TaoWind OPP 验证、文明握手与桥编译工具 / validator, handshake and bridge compiler")
    sub=parser.add_subparsers(dest="command",required=True)
    p_validate=sub.add_parser("validate",help="验证现实信封 / validate envelope"); p_validate.add_argument("file")
    p_handshake=sub.add_parser("handshake",help="协商两个 CHP offer / negotiate two CHP offers"); p_handshake.add_argument("local"); p_handshake.add_argument("remote")
    p_bridge=sub.add_parser("bridge",help="扫描或编译外部协议资产 / scan or compile external protocol assets")
    bsub=p_bridge.add_subparsers(dest="bridge_command",required=True)
    p_scan=bsub.add_parser("scan",help="静态扫描，不执行源码 / static scan, never execute source")
    p_scan.add_argument("source"); p_scan.add_argument("--profile",default="auto",choices=["auto","generic","rcl","rncs","dwac"]); p_scan.add_argument("--source-id"); p_scan.add_argument("--max-files",type=int,default=5000); p_scan.add_argument("--max-bytes",type=int,default=50_000_000); p_scan.add_argument("--out")
    p_compile=bsub.add_parser("compile",help="生成 OPP 桥接包 / emit OPP bridge bundle")
    p_compile.add_argument("source"); p_compile.add_argument("--out",required=True); p_compile.add_argument("--profile",default="auto",choices=["auto","generic","rcl","rncs","dwac"]); p_compile.add_argument("--source-id"); p_compile.add_argument("--max-findings",type=int,default=5000)
    args=parser.parse_args(argv)
    if args.command=="bridge": return _bridge_cmd(args)
    if args.command=="validate":
        issues=validate_envelope(load(args.file))
        if issues:
            print(json.dumps({"status":"FAIL","状态":"失败","issues":[i.__dict__ for i in issues]},ensure_ascii=False,indent=2)); return 1
        print(json.dumps({"status":"PASS","状态":"通过","boundary":"结构通过不等于现实主张为真 / structural validation is not truth validation"},ensure_ascii=False,indent=2)); return 0
    result=negotiate_handshake(load(args.local),load(args.remote)); print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
