from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from opp.bridge import scan_repository, compile_bridge
from opp.integrity import content_root
from opp.registry import repository_root
from opp.validation import validate_envelope
ROOT=repository_root(); FIX=ROOT/'examples'/'bridge-fixtures'

class BridgeCompilerTests(unittest.TestCase):
    def test_profiles_and_discovery(self):
        rcl=scan_repository(FIX/'rcl',profile='auto'); self.assertEqual('rcl',rcl.profile); self.assertTrue(any(f.kind=='protocol' and f.native_id=='rcl.test-protocol.v0.1' for f in rcl.findings))
        dwac=scan_repository(FIX/'dwac',profile='auto'); self.assertEqual('dwac',dwac.profile); self.assertTrue(any(f.native_id=='dwac.worker-protocol.v0.2' for f in dwac.findings))
    def test_does_not_execute_python(self):
        marker=FIX/'dwac'/'SHOULD_NOT_EXIST'; marker.unlink(missing_ok=True); scan_repository(FIX/'dwac'); self.assertFalse(marker.exists())
    def test_compile_emits_valid_opp_envelopes(self):
        result=compile_bridge(FIX/'rcl',source_id='fixture-rcl',profile='rcl')
        self.assertTrue(result['manifest']['validation']['valid'])
        for env in [*result['evidence'],*result['artifacts'],*result['capabilities'],result['handshake']]: self.assertEqual([],validate_envelope(env))
        self.assertEqual([],result['handshake']['payload']['authorityScopes'])
        self.assertTrue(all(x['payload']['authorityRequired']==[] for x in result['capabilities']))
    def test_deterministic_same_source(self):
        a=compile_bridge(FIX/'rcl',source_id='fixture-rcl',profile='rcl'); b=compile_bridge(FIX/'rcl',source_id='fixture-rcl',profile='rcl')
        self.assertEqual(a['manifest']['manifestRoot'],b['manifest']['manifestRoot']); self.assertEqual([x['integrity']['contentRoot'] for x in a['capabilities']],[x['integrity']['contentRoot'] for x in b['capabilities']])
    def test_manifest_and_scan_schemas(self):
        result=compile_bridge(FIX/'rncs',source_id='fixture-rncs',profile='rncs')
        for name,obj in [('bridge-scan.schema.json',result['scan']),('bridge-manifest.schema.json',result['manifest'])]:
            schema=json.loads((ROOT/'schemas'/name).read_text(encoding='utf-8')); self.assertEqual([],list(Draft202012Validator(schema).iter_errors(obj)))
    def test_cli_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            p=subprocess.run([sys.executable,'-m','opp','bridge','compile',str(FIX/'dwac'),'--out',td,'--profile','dwac'],capture_output=True,text=True)
            self.assertEqual(0,p.returncode,p.stderr+p.stdout); self.assertTrue((Path(td)/'manifest.json').exists()); self.assertTrue((Path(td)/'handshake.json').exists())
    def test_symlink_is_not_followed(self):
        if not hasattr(Path, "symlink_to"):
            self.skipTest("symlink unsupported")
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            Path(outside,"secret.mjs").write_text("export const SECRET_PROTOCOL_FORMAT = 'opp.secret-protocol.v0.1';",encoding="utf-8")
            link=Path(td,"escape.mjs")
            try: link.symlink_to(Path(outside,"secret.mjs"))
            except OSError: self.skipTest("symlink creation unavailable")
            r=scan_repository(td,profile="generic")
            self.assertEqual([],r.findings)
            self.assertTrue(any(x.startswith("SYMLINK_SKIPPED:") for x in r.warnings))

    def test_unknown_plain_repo_stays_generic(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td,'note.txt').write_text('hello world',encoding='utf-8'); r=scan_repository(td); self.assertEqual('generic',r.profile); self.assertEqual([],r.findings)

if __name__=='__main__': unittest.main()
