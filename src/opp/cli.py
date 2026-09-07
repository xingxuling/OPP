"""OPP CLI（命令行接口）。"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from .handshake import negotiate_handshake
from .validation import validate_envelope


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="TaoWind OPP 验证与文明握手工具 / validator and handshake tool")
    sub = parser.add_subparsers(dest="command", required=True)
    p_validate = sub.add_parser("validate", help="验证现实信封 / validate envelope")
    p_validate.add_argument("file")
    p_handshake = sub.add_parser("handshake", help="协商两个 CHP offer / negotiate two CHP offers")
    p_handshake.add_argument("local")
    p_handshake.add_argument("remote")
    args = parser.parse_args(argv)

    if args.command == "validate":
        issues = validate_envelope(load(args.file))
        if issues:
            print(json.dumps({"status":"FAIL","状态":"失败","issues":[i.__dict__ for i in issues]}, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps({"status":"PASS","状态":"通过","boundary":"结构通过不等于现实主张为真 / structural validation is not truth validation"}, ensure_ascii=False, indent=2))
        return 0

    result = negotiate_handshake(load(args.local), load(args.remote))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
