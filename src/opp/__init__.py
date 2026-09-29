"""TaoWind OPP（道风开放现实协议族）候选参考实现。"""

from .integrity import canonical_json_bytes, content_root, seal_envelope, verify_envelope_root
from .validation import validate_envelope, ValidationIssue
from .handshake import negotiate_handshake
from .capability import negotiate_capability
from .action import (
    ACTION_FORMAT, KNOWN_EFFECTS, ActionContractError,
    build_action_contract, verify_action_contract,
)

__version__ = "0.3.0-candidate.1"
__all__ = [
    "canonical_json_bytes", "content_root", "seal_envelope", "verify_envelope_root",
    "validate_envelope", "ValidationIssue", "negotiate_handshake", "negotiate_capability",
    "ACTION_FORMAT", "KNOWN_EFFECTS", "ActionContractError",
    "build_action_contract", "verify_action_contract",
]
