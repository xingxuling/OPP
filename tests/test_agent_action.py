from opp.agent_action import AgentActionContractError, compile_agent_action_contract, verify_agent_action_contract


def test_read_only_contract_is_descriptive_and_rooted():
    contract = compile_agent_action_contract(
        action_id="agent.read-workspace",
        operations=["filesystem.read"],
        targets=["workspace:README.md"],
        reversibility="reversible",
    ).as_dict()
    assert contract["authorities"] == ["workspace.read"]
    assert contract["authorityGranted"] is False
    assert contract["executable"] is False
    assert verify_agent_action_contract(contract)


def test_npm_with_lifecycle_script_exposes_hidden_process_authority():
    contract = compile_agent_action_contract(
        action_id="agent.install-package",
        operations=["package.install", "package.lifecycle-script"],
        targets=["workspace:package.json"],
        network_destinations=["registry.npmjs.org"],
        reversibility="partial",
    ).as_dict()
    assert set(contract["authorities"]) == {"package.install", "workspace.write", "network.egress", "process.spawn"}
    assert "process.spawn" in contract["sideEffects"]
    assert verify_agent_action_contract(contract)


def test_git_push_requires_scm_write_and_egress():
    contract = compile_agent_action_contract(
        action_id="agent.push",
        operations=["scm.write"],
        network_destinations=["github.com"],
        reversibility="partial",
        human_approval_required=True,
    ).as_dict()
    assert set(contract["authorities"]) == {"scm.write", "network.egress"}
    assert contract["humanApprovalRequired"] is True


def test_unknown_operation_fails_closed():
    try:
        compile_agent_action_contract(action_id="x", operations=["magic.root-shell"])
    except AgentActionContractError as error:
        assert "unknown operation" in str(error)
    else:
        raise AssertionError("unknown operation must fail closed")


def test_contract_tamper_is_detected():
    contract = compile_agent_action_contract(action_id="x", operations=["filesystem.read"]).as_dict()
    contract["authorities"] = ["credential.read"]
    assert not verify_agent_action_contract(contract)
