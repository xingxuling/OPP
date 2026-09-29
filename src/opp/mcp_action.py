"""Bind an MCP tools/list declaration to an OPP Agent Action Contract.

MCP annotations remain hints. Security authority/effect/resource declarations are
explicit caller/provider assertions and are never inferred from annotations alone.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from .action import build_action_contract, verify_action_contract
from .integrity import content_root
from .surfaces import describe_mcp_tool

MCP_ACTION_BINDING_FORMAT = "taowind.opp.mcp-action-binding.v0.1"


class MCPActionBindingError(ValueError):
    """Stable failure code for MCP action binding verification."""


def _tool(tool: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(tool, Mapping):
        raise MCPActionBindingError("MCP_TOOL_OBJECT_REQUIRED")
    value = deepcopy(dict(tool))
    name = value.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 256:
        raise MCPActionBindingError("MCP_TOOL_NAME_INVALID")
    if not isinstance(value.get("inputSchema"), Mapping):
        raise MCPActionBindingError("MCP_TOOL_INPUT_SCHEMA_REQUIRED")
    if "outputSchema" in value and value["outputSchema"] is not None and not isinstance(value["outputSchema"], Mapping):
        raise MCPActionBindingError("MCP_TOOL_OUTPUT_SCHEMA_INVALID")
    return value


def bind_mcp_tool_action(
    tool: Mapping[str, Any], *,
    participant: str,
    binding_id: str,
    revision: str,
    action_id: str,
    authority_required: Iterable[str],
    side_effects: Iterable[str],
    reversibility: str,
    accepted_effects: Iterable[str],
    resources: Mapping[str, Any] | None = None,
    resource_bindings: Mapping[str, Iterable[str]] | None = None,
    statefulness: str = "unknown",
) -> dict[str, Any]:
    """Create a rooted MCP -> RCP -> Agent Action binding.

    The raw tools/list declaration is bound by content root. MCP annotations are
    preserved inside the tool root but do not grant authority, prove read-only
    behavior, or override explicit side-effect declarations.
    """
    tool_value = _tool(tool)
    if not isinstance(participant, str) or not participant.strip():
        raise MCPActionBindingError("MCP_PARTICIPANT_REQUIRED")
    if not isinstance(binding_id, str) or not binding_id.strip():
        raise MCPActionBindingError("MCP_BINDING_ID_REQUIRED")
    if not isinstance(revision, str) or not revision.strip():
        raise MCPActionBindingError("MCP_REVISION_REQUIRED")
    if reversibility not in {"reversible", "compensatable", "irreversible", "unknown"}:
        raise MCPActionBindingError("MCP_REVERSIBILITY_INVALID")

    declaration = describe_mcp_tool(
        tool_value,
        participant=participant.strip(),
        surface={"bindingId": binding_id.strip(), "revision": revision.strip()},
        semantics={"input": {}, "output": {}},
        authority_required=tuple(authority_required),
        side_effects=tuple(side_effects),
        statefulness=statefulness,
        reversibility=reversibility,
    )
    contract = build_action_contract(
        declaration,
        action_id=action_id,
        accepted_effects=accepted_effects,
        resources=resources,
    )
    resource_bindings = {} if resource_bindings is None else resource_bindings
    if not isinstance(resource_bindings, Mapping):
        raise MCPActionBindingError("MCP_RESOURCE_BINDINGS_INVALID")
    allowed_resource_keys = {"filesystem", "network", "commands", "packages"}
    if set(resource_bindings) - allowed_resource_keys:
        raise MCPActionBindingError("MCP_RESOURCE_BINDING_KEY_UNKNOWN")
    normalized_bindings: dict[str, list[str]] = {}
    input_properties = tool_value["inputSchema"].get("properties", {})
    if not isinstance(input_properties, Mapping):
        raise MCPActionBindingError("MCP_TOOL_INPUT_PROPERTIES_REQUIRED")
    for key in sorted(allowed_resource_keys):
        fields = resource_bindings.get(key, ())
        if isinstance(fields, (str, bytes)):
            raise MCPActionBindingError(f"MCP_RESOURCE_BINDING_ARRAY_REQUIRED:{key}")
        values = []
        for field in fields:
            if not isinstance(field, str) or not field.strip() or field not in input_properties:
                raise MCPActionBindingError(f"MCP_RESOURCE_BINDING_FIELD_INVALID:{key}")
            values.append(field.strip())
        normalized_bindings[key] = sorted(set(values))
    for key, values in contract["resources"].items():
        if values and not normalized_bindings.get(key):
            raise MCPActionBindingError(f"MCP_RESOURCE_BINDING_REQUIRED:{key}")

    body = {
        "format": MCP_ACTION_BINDING_FORMAT,
        "toolName": tool_value["name"],
        "mcpToolRoot": content_root(tool_value),
        "capabilityDeclaration": declaration,
        "capabilityRoot": content_root(declaration),
        "actionContract": contract,
        "actionContractRoot": contract["contractRoot"],
        "resourceBindings": normalized_bindings,
        "authorityGranted": False,
        "annotationsTrusted": False,
        "boundary": (
            "MCP tool annotations are descriptive hints only. This binding does not "
            "authenticate the server, grant authority, prove sandboxing, or prove that "
            "runtime side effects match the declaration."
        ),
    }
    return {**body, "bindingRoot": content_root(body)}


def verify_mcp_action_binding(
    binding: Mapping[str, Any], *,
    tool: Mapping[str, Any] | None = None,
    expected_root: str | None = None,
) -> bool:
    if not isinstance(binding, Mapping):
        raise MCPActionBindingError("MCP_ACTION_BINDING_OBJECT_REQUIRED")
    root = binding.get("bindingRoot")
    body = {k: deepcopy(v) for k, v in binding.items() if k != "bindingRoot"}
    if body.get("format") != MCP_ACTION_BINDING_FORMAT or root != content_root(body):
        raise MCPActionBindingError("MCP_ACTION_BINDING_ROOT_INVALID")
    if expected_root is not None and root != expected_root:
        raise MCPActionBindingError("MCP_ACTION_BINDING_EXPECTED_ROOT_MISMATCH")
    if body.get("authorityGranted") is not False or body.get("annotationsTrusted") is not False:
        raise MCPActionBindingError("MCP_ACTION_BINDING_TRUST_BOUNDARY_INVALID")
    resource_bindings = body.get("resourceBindings")
    if not isinstance(resource_bindings, Mapping) or set(resource_bindings) != {"commands", "filesystem", "network", "packages"}:
        raise MCPActionBindingError("MCP_ACTION_RESOURCE_BINDINGS_INVALID")
    input_properties = body.get("capabilityDeclaration", {}).get("payload", {}).get("inputSchema", {}).get("properties", {})
    if not isinstance(input_properties, Mapping):
        raise MCPActionBindingError("MCP_ACTION_INPUT_PROPERTIES_INVALID")
    for key, fields in resource_bindings.items():
        if not isinstance(fields, list) or any(not isinstance(field, str) or field not in input_properties for field in fields):
            raise MCPActionBindingError(f"MCP_ACTION_RESOURCE_BINDING_FIELD_INVALID:{key}")
    declaration = body.get("capabilityDeclaration")
    contract = body.get("actionContract")
    if content_root(declaration) != body.get("capabilityRoot"):
        raise MCPActionBindingError("MCP_ACTION_CAPABILITY_ROOT_MISMATCH")
    if contract.get("contractRoot") != body.get("actionContractRoot"):
        raise MCPActionBindingError("MCP_ACTION_CONTRACT_ROOT_MISMATCH")
    verify_action_contract(contract, capability=declaration, expected_root=body["actionContractRoot"])
    for key, values in contract.get("resources", {}).items():
        if values and not resource_bindings.get(key):
            raise MCPActionBindingError(f"MCP_ACTION_RESOURCE_BINDING_REQUIRED:{key}")
    if contract.get("capabilityId") != body.get("toolName"):
        raise MCPActionBindingError("MCP_ACTION_TOOL_CAPABILITY_MISMATCH")
    if tool is not None:
        tool_value = _tool(tool)
        if content_root(tool_value) != body.get("mcpToolRoot"):
            raise MCPActionBindingError("MCP_ACTION_TOOL_ROOT_MISMATCH")
        if tool_value["name"] != body.get("toolName"):
            raise MCPActionBindingError("MCP_ACTION_TOOL_NAME_MISMATCH")
    return True


__all__ = [
    "MCP_ACTION_BINDING_FORMAT", "MCPActionBindingError",
    "bind_mcp_tool_action", "verify_mcp_action_binding",
]
