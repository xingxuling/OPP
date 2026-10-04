import copy
import json
import tempfile
import unittest
import os
import subprocess
import sys
from pathlib import Path
from jsonschema import Draft202012Validator
from opp.integrity import content_root, canonical_json_bytes, BINARY64_CANONICAL_PROFILE
from opp.runtime import run_interop, InteropError
from opp.runtime.verification import verify_interop_result
from opp.registry import read_json_resource

PROFILE = BINARY64_CANONICAL_PROFILE
VECTORS = json.loads((Path(__file__).parent / 'fixtures/native-canonical-vectors.json').read_text(encoding='utf-8'))

class NativeCanonicalTests(unittest.TestCase):
    def test_fixed_canonical_vectors(self):
        for vector in VECTORS['vectors']:
            with self.subTest(vector=vector['name']):
                self.assertEqual(vector['canonical'].encode('utf-8'), canonical_json_bytes(vector['value'], profile=PROFILE))
                self.assertEqual(vector['root'], content_root(vector['value'], profile=PROFILE))
                self.assertEqual(vector['legacyPythonRoot'], content_root(vector['value']))

    def test_numeric_limits_types_and_unknown_profile(self):
        for value in (float('nan'), float('inf'), -float('inf'), 9007199254740992, 10 ** 1000):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(ValueError): content_root(value, profile=PROFILE)
        with self.assertRaises(ValueError): content_root('\ud800', profile=PROFILE)
        with self.assertRaises(ValueError): content_root({}, profile='unknown')
        self.assertEqual(content_root(20, profile=PROFILE), content_root(20.0, profile=PROFILE))
        self.assertEqual(content_root(0, profile=PROFILE), content_root(-0.0, profile=PROFILE))
        self.assertNotEqual(content_root(20, profile=PROFILE), content_root('20', profile=PROFILE))
        self.assertNotEqual(content_root(None, profile=PROFILE), content_root(['null'], profile=PROFILE))

    def test_real_invocations_and_explicit_profile_verification(self):
        with tempfile.TemporaryDirectory(prefix='opp-canonical-test-') as directory:
            Path(directory, 'fixture.py').write_text('def echo(value):\n    return {"value": value}\n', encoding='utf-8')
            def spec(role):
                return {'format': 'taowind.opp.invocation-spec.v0.1', 'version': '0.3.0-candidate.1', 'specId': role,
                        'adapterKind': 'python-function', 'sourceRoot': directory, 'entrypoint': 'fixture.py:echo',
                        'callingConvention': 'kwargs', 'timeoutMs': 3000, 'maxOutputBytes': 262144,
                        'cwdPolicy': 'ephemeral', 'environmentPolicy': 'sanitized', 'authorityRequired': [], 'status': 'candidate'}
            plan = {'status': 'candidate', 'executionModel': 'opp-declarative-json-transform', 'operations': []}
            plan['planRoot'] = content_root(plan)
            run = {'format': 'taowind.opp.interop-run.v0.1', 'runId': 'profile-regression', 'producer': spec('producer'),
                   'consumer': spec('consumer'), 'bridgePlan': plan, 'status': 'candidate'}
            for value in (20, 20.0, -0.0, 1e-7, 20.5, 9007199254740991, '\u9053\u98ce\U0001f30f'):
                with self.subTest(value=value):
                    result = run_interop(run, {'value': value}, allow_execution=True, canonical_profile=PROFILE)
                    self.assertTrue(verify_interop_result(result, run, {'value': value}, canonical_profile=PROFILE))
                    self.assertEqual('taowind.opp.interop-receipt.v0.2', result['receipt']['format'])
                    self.assertEqual(PROFILE, result['receipt']['canonicalProfile'])
                    for role in ('producer', 'consumer'):
                        self.assertTrue(Draft202012Validator(read_json_resource('schemas/invocation-receipt.v0.2.schema.json')).is_valid(result[role]['receipt']))
                    with self.assertRaises(InteropError): verify_interop_result(result, run, {'value': value})
            legacy = run_interop(run, {'value': 20}, allow_execution=True)
            self.assertEqual('taowind.opp.interop-receipt.v0.1', legacy['receipt']['format'])
            self.assertNotIn('canonicalProfile', legacy['receipt'])
            self.assertTrue(verify_interop_result(legacy, run, {'value': 20}))
            with self.assertRaises(InteropError): verify_interop_result(legacy, run, {'value': 20}, canonical_profile=PROFILE)

            for role in ('producer', 'consumer'):
                for mutate in (lambda receipt: receipt['authority'].pop('required'),
                               lambda receipt: receipt['authority'].__setitem__('required', [1]),
                               lambda receipt: receipt.__setitem__('boundary', 42)):
                    forged = copy.deepcopy(result)
                    mutate(forged[role]['receipt'])
                    stable = {key: item for key, item in forged[role]['receipt'].items() if key not in ('receiptRoot', 'durationMs')}
                    forged[role]['receipt']['receiptRoot'] = content_root(stable, profile=PROFILE)
                    forged['receipt'][role + 'ReceiptRoot'] = forged[role]['receipt']['receiptRoot']
                    forged['receipt']['receiptRoot'] = content_root({key: item for key, item in forged['receipt'].items() if key != 'receiptRoot'}, profile=PROFILE)
                    with self.assertRaises(InteropError): verify_interop_result(forged, run, {'value': value}, canonical_profile=PROFILE)

    def test_new_schemas_are_packaged_identically(self):
        root = Path(__file__).resolve().parents[1]
        for kind in ('invocation', 'interop'):
            name = kind + '-receipt.v0.2.schema.json'
            self.assertEqual((root / 'schemas' / name).read_bytes(), (root / 'src/opp/resources/schemas' / name).read_bytes())

    def test_cli_profile_is_explicit_and_unknown_profile_cannot_execute(self):
        root = Path(__file__).resolve().parents[1]
        env = {**os.environ, 'PYTHONPATH': str(root / 'src'), 'PYTHONDONTWRITEBYTECODE': '1'}
        with tempfile.TemporaryDirectory(prefix='opp-profile-cli-') as directory:
            folder = Path(directory)
            (folder / 'fixture.py').write_text('def echo(value):\n    return {"value": value}\n', encoding='utf-8')
            spec = {'format': 'taowind.opp.invocation-spec.v0.1', 'version': '0.3.0-candidate.1', 'specId': 'cli',
                    'adapterKind': 'python-function', 'sourceRoot': directory, 'entrypoint': 'fixture.py:echo',
                    'callingConvention': 'kwargs', 'timeoutMs': 3000, 'maxOutputBytes': 262144,
                    'cwdPolicy': 'ephemeral', 'environmentPolicy': 'sanitized', 'authorityRequired': [], 'status': 'candidate'}
            plan = {'status': 'candidate', 'executionModel': 'opp-declarative-json-transform', 'operations': []}
            plan['planRoot'] = content_root(plan)
            run = {'format': 'taowind.opp.interop-run.v0.1', 'runId': 'cli-profile', 'producer': spec, 'consumer': spec,
                   'bridgePlan': plan, 'status': 'candidate'}
            files = [folder / name for name in ('run.json', 'input.json', 'result.json')]
            files[0].write_text(json.dumps(run), encoding='utf-8')
            files[1].write_text(json.dumps({'value': 1e-7}), encoding='utf-8')
            command = [sys.executable, '-X', 'utf8', '-m', 'opp', 'interop', 'run', str(files[0]), str(files[1]), '--allow-execution', '--out', str(files[2])]
            child = subprocess.run(command + ['--canonical-profile', 'unknown'], cwd=root, env=env, capture_output=True, text=True)
            self.assertNotEqual(0, child.returncode)
            self.assertFalse(files[2].exists())
            child = subprocess.run(command + ['--canonical-profile', PROFILE], cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(0, child.returncode, child.stderr)
            verify = [sys.executable, '-X', 'utf8', '-m', 'opp', 'interop', 'verify', *map(str, files)]
            child = subprocess.run(verify + ['--canonical-profile', PROFILE], cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(0, child.returncode, child.stderr)
            child = subprocess.run(verify, cwd=root, env=env, capture_output=True, text=True)
            self.assertNotEqual(0, child.returncode)
