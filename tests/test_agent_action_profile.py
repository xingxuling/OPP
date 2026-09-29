import copy
import unittest
from opp.action_profile import ActionProfileError, negotiate_agent_action, verify_agent_action_contract

class AgentActionProfileTests(unittest.TestCase):
    def provider(self):
        return {
            "providerId":"provider:code-workspace",
            "actions":["filesystem.read","network.egress","package.inspect"],
            "resourceScopes":["workspace:/src/*","package:npm/*","https://api.github.com/*"],
            "networkHosts":["api.github.com"],
            "sideEffects":["none","read","network"],
            "reversibility":["none","reversible","unknown"],
            "authorityRequired":["workspace.read"],
        }

    def request(self, **patch):
        base={"action":"filesystem.read","resource":"workspace:/src/app.py","sideEffect":"read",
              "reversibility":"none","dataClasses":["source-code"],"origin":"agent:code"}
        base.update(patch)
        return base

    def test_direct_contract_never_grants_authority(self):
        result=negotiate_agent_action(self.request(),self.provider())
        self.assertEqual(result["outcome"],"DIRECT")
        self.assertFalse(result["authorityGranted"])
        self.assertFalse(result["contract"]["authorityGranted"])
        self.assertEqual(result["contract"]["requiredAuthority"],["workspace.read"])
        self.assertTrue(verify_agent_action_contract(result))

    def test_credential_read_is_rejected(self):
        result=negotiate_agent_action(self.request(action="credential.read",resource="home:~/.ssh/id_rsa"),self.provider())
        self.assertEqual(result["outcome"],"REJECT")
        self.assertIn("ACTION_UNSUPPORTED",result["reasons"])

    def test_network_host_must_be_explicitly_declared(self):
        allowed=negotiate_agent_action(self.request(action="network.egress",resource="https://api.github.com/repos/x/y",
            networkHost="api.github.com",sideEffect="network"),self.provider())
        self.assertEqual(allowed["outcome"],"DIRECT")
        denied=negotiate_agent_action(self.request(action="network.egress",resource="https://evil.example/exfil",
            networkHost="evil.example",sideEffect="network"),self.provider())
        self.assertEqual(denied["outcome"],"REJECT")

    def test_side_effect_and_reversibility_are_not_silently_weakened(self):
        self.assertEqual(negotiate_agent_action(self.request(sideEffect="write"),self.provider())["outcome"],"REJECT")
        self.assertEqual(negotiate_agent_action(self.request(reversibility="irreversible"),self.provider())["outcome"],"NEGOTIATE")

    def test_tampered_root_fails_verification(self):
        result=negotiate_agent_action(self.request(),self.provider())
        tampered=copy.deepcopy(result); tampered["contract"]["resource"]="workspace:/src/other.py"
        with self.assertRaises(ActionProfileError):
            verify_agent_action_contract(tampered)

if __name__=="__main__":
    unittest.main()
