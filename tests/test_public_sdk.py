import copy
import tempfile
import unittest
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch
from opp.sdk import (SDK_API_VERSION, SemanticPort, InvocationSpec, synthesize_bridge,
                     run_interop, verify_interop_result, InteropError, compare_ports)


class PublicSdkTests(unittest.TestCase):
    def test_unknown_types_do_not_become_exact(self):
        a = SemanticPort('a', 'a', 'output', {})
        b = SemanticPort('b', 'b', 'input', {})
        self.assertEqual('unknown', compare_ports(a, b).classification)
        self.assertEqual('rejected', synthesize_bridge(a, b)['status'])

    def test_installed_surface_bound_verification_and_tampering(self):
        self.assertEqual(1, SDK_API_VERSION)
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'adapter.py').write_text('def invoke(value):\n    return {"value": value}\n', encoding='utf-8')
            shape = {'type': 'object', 'properties': {'value': {'type': 'string'}}, 'required': ['value']}
            plan = synthesize_bridge(SemanticPort('a', 'a', 'output', shape), SemanticPort('b', 'b', 'input', shape))
            spec = InvocationSpec('external', 'python-function', directory, 'adapter.py:invoke').to_dict()
            run = {'format': 'taowind.opp.interop-run.v0.1', 'runId': 'sdk', 'producer': spec, 'consumer': spec, 'bridgePlan': plan}
            payload = {'value': '真实第三方🌏'}
            result = run_interop(run, payload, allow_execution=True)
            for name, value in [('spec', run), ('input', payload), ('result', result)]:
                Path(directory, name + '.json').write_text(json.dumps(value), encoding='utf-8')
            completed = subprocess.run([sys.executable, '-m', 'opp', 'interop', 'verify',
                *[str(Path(directory, name + '.json')) for name in ['spec', 'input', 'result']]], capture_output=True, text=True)
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertEqual(0, json.loads(completed.stdout)['targetExecutions'])
            with patch('subprocess.Popen', side_effect=AssertionError('verification must be offline')):
                self.assertTrue(verify_interop_result(result, run, payload))
            # Existing Auto Connect reports wrap the sealed plan with provenance.
            wrapped = copy.deepcopy(run)
            wrapped['bridgePlan'].update(producerInterface={'operation': 'invoke'}, consumerInterface={'operation': 'invoke'})
            wrapped_result = run_interop(wrapped, payload, allow_execution=True)
            self.assertTrue(verify_interop_result(wrapped_result, wrapped, payload))
            for mutated_run, mutated_input, mutated_result in [
                (run, {'value': 'changed'}, result),
                (run, payload, {**result, 'result': {'value': 'changed'}}),
                ({**run, 'runId': 'changed'}, payload, result),
            ]:
                with self.assertRaises(InteropError):
                    verify_interop_result(mutated_result, mutated_run, mutated_input)
            tampered = copy.deepcopy(run)
            tampered['bridgePlan']['operations'] = []
            with patch('subprocess.Popen', side_effect=AssertionError('no invocation on tampered plan')):
                with self.assertRaisesRegex(InteropError, 'BRIDGE_PLAN_ROOT_INVALID'):
                    run_interop(tampered, payload, allow_execution=True)
