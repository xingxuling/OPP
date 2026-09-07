"""OPP Bridge Compiler public API（桥编译器公共接口）。"""
from .model import PrimitiveFinding, ScanReport, SourceRef
from .profiles import PROFILES, BridgeProfile, detect_profile
from .scanner import scan_repository
from .compiler import compile_bridge, write_bridge_bundle
__all__=["PrimitiveFinding","ScanReport","SourceRef","PROFILES","BridgeProfile","detect_profile","scan_repository","compile_bridge","write_bridge_bundle"]
