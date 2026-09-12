"""Versioned public entry point for OPP's existing candidate implementations.

No repository import path, network client, or new negotiation owner is needed.
Execution remains opt-in. See docs/PUBLIC_SDK.md for supported boundaries.
"""
from . import (
    canonical_json_bytes, content_root, seal_envelope, verify_envelope_root,
    validate_envelope, negotiate_handshake, negotiate_capability,
)
from .bridge import (
    verify_repository_semantics, plan_repository_connection, compare_ports,
    synthesize_bridge, apply_transform,
)
from .bridge.semantic_model import SemanticPort
from .runtime import run_invocation, run_interop, InvocationError, InteropError
from .runtime.model import InvocationSpec
from .runtime.verification import verify_interop_result

SDK_API_VERSION = 1
__all__ = [
    'SDK_API_VERSION', 'canonical_json_bytes', 'content_root', 'seal_envelope',
    'verify_envelope_root', 'validate_envelope', 'negotiate_handshake',
    'negotiate_capability', 'verify_repository_semantics',
    'plan_repository_connection', 'compare_ports', 'synthesize_bridge',
    'apply_transform', 'SemanticPort', 'InvocationSpec', 'run_invocation',
    'run_interop', 'InvocationError', 'InteropError', 'verify_interop_result',
]
