from copy import deepcopy

import pytest

from opp.mcp_action import MCPActionBindingError, bind_mcp_tool_action, verify_mcp_action_binding


def tool(name="workspace.read"):
    return {
        "name": name,
        "description": "Read one bounded workspace file",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    }


def test_mcp_tool_binds_to_rooted_agent_action_contract():
    raw = tool()
    binding = bind_mcp_tool_action(
        raw,
        participant="mcp:workspace",
        binding_id="server:workspace",
        revision="1",
        action_id="action:mcp-workspace-read",
        authority_required=["workspace.read"],
        side_effects=[],
        reversibility="reversible",
        accepted_effects=["filesystem.read"],
        resources={"filesystem": ["workspace/project/readme.md"]},
        resource_bindings={"filesystem": ["path"]},
        statefulness="stateless",
    )
    assert binding["authorityGranted"] is False
    assert binding["annotationsTrusted"] is False
    assert binding["actionContract"]["declaredEffects"] == ["filesystem.read"]
    assert binding["actionContract"]["status"] == "accepted"
    assert verify_mcp_action_binding(binding, tool=raw)


def test_mcp_annotations_do_not_grant_authority_or_remove_resource_binding():
    raw = tool()
    binding = bind_mcp_tool_action(
        raw,
        participant="mcp:workspace",
        binding_id="server:workspace",
        revision="1",
        action_id="action:mcp-workspace-read",
        authority_required=["workspace.read"],
        side_effects=[],
        reversibility="reversible",
        accepted_effects=[],
        resources={},
        resource_bindings={},
        statefulness="stateless",
    )
    assert binding["actionContract"]["status"] == "negotiate"
    assert "EFFECT_ACKNOWLEDGEMENT_MISMATCH" in binding["actionContract"]["reasons"]
    assert "RESOURCE_BINDING_REQUIRED:filesystem.read" in binding["actionContract"]["reasons"]


def test_tool_descriptor_drift_is_detected():
    raw = tool()
    binding = bind_mcp_tool_action(
        raw,
        participant="mcp:workspace",
        binding_id="server:workspace",
        revision="1",
        action_id="action:mcp-workspace-read",
        authority_required=["workspace.read"],
        side_effects=[],
        reversibility="reversible",
        accepted_effects=["filesystem.read"],
        resources={"filesystem": ["workspace/project/readme.md"]},
        resource_bindings={"filesystem": ["path"]},
        statefulness="stateless",
    )
    drifted = deepcopy(raw)
    drifted["inputSchema"]["properties"]["path"]["maxLength"] = 32
    with pytest.raises(MCPActionBindingError, match="TOOL_ROOT_MISMATCH"):
        verify_mcp_action_binding(binding, tool=drifted)


def test_binding_tamper_fails_closed():
    raw = tool()
    binding = bind_mcp_tool_action(
        raw,
        participant="mcp:workspace",
        binding_id="server:workspace",
        revision="1",
        action_id="action:mcp-workspace-read",
        authority_required=["workspace.read"],
        side_effects=[],
        reversibility="reversible",
        accepted_effects=["filesystem.read"],
        resources={"filesystem": ["workspace/project/readme.md"]},
        resource_bindings={"filesystem": ["path"]},
        statefulness="stateless",
    )
    binding["toolName"] = "shell.exec"
    with pytest.raises(MCPActionBindingError, match="BINDING_ROOT_INVALID"):
        verify_mcp_action_binding(binding)


def test_nonempty_contract_resource_requires_argument_binding():
    raw = tool()
    with pytest.raises(MCPActionBindingError, match="RESOURCE_BINDING_REQUIRED:filesystem"):
        bind_mcp_tool_action(
            raw,
            participant="mcp:workspace",
            binding_id="server:workspace",
            revision="1",
            action_id="action:mcp-workspace-read",
            authority_required=["workspace.read"],
            side_effects=[],
            reversibility="reversible",
            accepted_effects=["filesystem.read"],
            resources={"filesystem": ["workspace/project/readme.md"]},
            resource_bindings={},
            statefulness="stateless",
        )


def test_resource_binding_must_reference_real_input_field():
    raw = tool()
    with pytest.raises(MCPActionBindingError, match="RESOURCE_BINDING_FIELD_INVALID:filesystem"):
        bind_mcp_tool_action(
            raw,
            participant="mcp:workspace",
            binding_id="server:workspace",
            revision="1",
            action_id="action:mcp-workspace-read",
            authority_required=["workspace.read"],
            side_effects=[],
            reversibility="reversible",
            accepted_effects=["filesystem.read"],
            resources={"filesystem": ["workspace/project/readme.md"]},
            resource_bindings={"filesystem": ["not_a_field"]},
            statefulness="stateless",
        )


def test_mcp_meta_is_not_part_of_semantic_tool_root():
    raw = tool()
    raw["_meta"] = {"taowind/bindingRoot": "placeholder", "host/debug": "mutable"}
    with_meta = bind_mcp_tool_action(
        raw,
        participant="mcp:workspace",
        binding_id="server:workspace",
        revision="1",
        action_id="action:mcp-workspace-read",
        authority_required=["workspace.read"],
        side_effects=[],
        reversibility="reversible",
        accepted_effects=["filesystem.read"],
        resources={"filesystem": ["workspace/project/readme.md"]},
        resource_bindings={"filesystem": ["path"]},
        statefulness="stateless",
    )
    without_meta = bind_mcp_tool_action(
        tool(),
        participant="mcp:workspace",
        binding_id="server:workspace",
        revision="1",
        action_id="action:mcp-workspace-read",
        authority_required=["workspace.read"],
        side_effects=[],
        reversibility="reversible",
        accepted_effects=["filesystem.read"],
        resources={"filesystem": ["workspace/project/readme.md"]},
        resource_bindings={"filesystem": ["path"]},
        statefulness="stateless",
    )
    assert with_meta["mcpToolRoot"] == without_meta["mcpToolRoot"]
    assert with_meta["mcpTool"] == without_meta["mcpTool"]
