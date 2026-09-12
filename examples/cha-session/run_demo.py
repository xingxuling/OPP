"""Actual Python -> HTTP and HTTP -> CLI calls using installed opp.sdk.

Run with: python examples/cha-session/run_demo.py --out <evidence-directory>
Three maintained libraries execute in operator-authored surface wrappers. These
are real local processes, NOT independent implementations/operators of OPP.
"""
import argparse
import hashlib
from http.client import HTTPConnection
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from opp.sdk import (InvocationSpec, SurfaceProvider, content_root, describe_openapi,
    describe_surface, negotiate_handshake, negotiate_session, run_invocation,
    run_session, seal_envelope, verify_repository_semantics, verify_session_receipt)

HERE = Path(__file__).resolve().parent
LIMIT = 65536
MEANING = {"concept": "urn:cha-demo:integer-sequence", "unit": "1"}


def command(file, argument=None, value=None):
    args = [sys.executable, "-I", str(HERE / file)]
    if argument:
        args.append(argument)
    proc = subprocess.run(args, input=None if value is None else json.dumps(value).encode("utf-8"),
                          capture_output=True, timeout=5, cwd=HERE,
                          env={k: os.environ[k] for k in ("SYSTEMROOT", "WINDIR") if k in os.environ})
    if proc.returncode or len(proc.stdout) > LIMIT:
        raise RuntimeError("CLI_FAILED_OR_OUTPUT_LIMIT")
    return json.loads(proc.stdout)


def http(port, method, path, value=None):
    client = HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        client.request(method, path, None if value is None else json.dumps(value),
                       {"Content-Type": "application/json"})
        response = client.getresponse()
        body = response.read(LIMIT + 1)
        if response.status != 200 or len(body) > LIMIT:
            raise RuntimeError(f"HTTP_STATUS_{response.status}")
        return json.loads(body)
    finally:
        client.close()


def offer(declaration):
    participant = declaration["issuer"]["id"]
    return seal_envelope({"format": "taowind.opp.reality-envelope.v0.1", "protocol": "opp.chp.v0.1",
        "version": "0.1.0-candidate.1", "kind": "protocol", "id": "offer:" + participant,
        "status": "candidate", "issuedAt": "1970-01-01T00:00:00Z", "issuer": declaration["issuer"],
        "payload": {"phase": "offer", "identity": {"id": participant, "civilizationType": "runtime"},
            "supportedProtocols": ["opp.chp.v0.1", "opp.rcp.v0.1"],
            "capabilities": [declaration["payload"]["capabilityId"]], "authorityScopes": [],
            "evidencePolicy": {"minimumConfidence": 0.0, "acceptDerivedEvidence": False,
                               "requiredProtocols": ["opp.chp.v0.1", "opp.rcp.v0.1"]}}})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-installed", action="store_true")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    import opp
    opp_path = str(Path(opp.__file__).resolve())
    if args.require_installed and "site-packages" not in Path(opp_path).parts:
        raise RuntimeError("INSTALLED_WHEEL_REQUIRED")
    artifacts = {}

    def save(name, value):
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        (out / name).write_bytes(raw)
        artifacts[name] = hashlib.sha256(raw).hexdigest()

    processes = []
    def start_http(reject=False):
        proc = subprocess.Popen([sys.executable, "-I", str(HERE / "http_actor.py")] +
            (["--reject-calls"] if reject else []), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=HERE, env={k: os.environ[k] for k in ("SYSTEMROOT", "WINDIR") if k in os.environ})
        processes.append(proc)
        # Bounded startup through a thread; no fixed sleep or guessed readiness.
        import queue
        import threading
        ready = queue.Queue()
        threading.Thread(target=lambda: ready.put(proc.stdout.readline()), daemon=True).start()
        return json.loads(ready.get(timeout=5))["port"]

    started = time.perf_counter()
    try:
        port = start_http()
        failing_port = start_http(True)
        raw_python, raw_cli = command("native_actor.py"), command("cli_actor.py", "--describe")
        raw_http = http(port, "GET", "/openapi.json")
        save("native-discovery.json", raw_python)
        save("cli-discovery.json", raw_cli)
        save("openapi-discovery.json", raw_http)
        save("static-semantic-scan.json", verify_repository_semantics(HERE, source_id="cha-actors").to_dict())
        # Reuse the previous external-project provenance collector.
        helper_path = HERE.parents[1] / "scripts" / "verify_external_projects.py"
        helper_spec = importlib.util.spec_from_file_location("opp_external_evidence", helper_path)
        helper = importlib.util.module_from_spec(helper_spec)
        helper_spec.loader.exec_module(helper)
        for package, module in (("boltons", "boltons"), ("jmespath", "jmespath"), ("more-itertools", "more_itertools")):
            _, provenance = helper.installed_source(package, module)
            save(package + "-source.json", provenance)
        native_receipts = []
        surface_calls = []

        def describe_native():
            raw = command("native_actor.py")
            return describe_surface(participant="python-boltons", capability_id=raw["name"],
                input_schema=raw["input"], output_schema=raw["output"], statefulness="stateless",
                surface={"kind": "python-function", "bindingId": "native", "revision": raw["revision"],
                         "discoveryRoot": content_root(raw)},
                semantics={"input": {"legacy_items": MEANING}, "output": {"unique_items": MEANING}})

        def call_native(value):
            spec = InvocationSpec("cha-native", "python-function", str(HERE), "native_actor.py:unique_numbers")
            result = run_invocation(spec.to_dict(), value, allow_execution=True)
            native_receipts.append(result)
            if result["receipt"]["status"] != "PASS":
                raise RuntimeError("NATIVE_INVOCATION_FAILED")
            return result["result"]

        def describe_http(target=None):
            return describe_openapi(http(port if target is None else target, "GET", "/openapi.json"), path="/sort",
                participant="http-jmespath", statefulness="stateless",
                surface={"bindingId": "http", "revision": "1"},
                semantics={"input": {"values": MEANING}, "output": {"ordered": MEANING}})

        def call_http(value, target=None):
            destination = port if target is None else target
            begin = time.perf_counter()
            try:
                result = http(destination, "POST", "/sort", value)
                surface_calls.append({"surface": "HTTP", "status": 200, "inputRoot": content_root(value),
                                      "outputRoot": content_root(result), "durationMs": (time.perf_counter()-begin)*1000})
                return result
            except RuntimeError as exc:
                surface_calls.append({"surface": "HTTP", "failure": str(exc), "inputRoot": content_root(value)})
                raise

        def describe_cli():
            raw = command("cli_actor.py", "--describe")
            return describe_surface(participant="cli-more-itertools", capability_id=raw["command"],
                input_schema=raw["stdin"], output_schema=raw["stdout"], statefulness="stateless",
                surface={"kind": "json-stdio-cli", "bindingId": "cli", "revision": raw["version"],
                         "discoveryRoot": content_root(raw)},
                semantics={"input": {"entries": MEANING}, "output": {"groups": {"concept": "urn:cha-demo:pairs", "unit": "1"}}})

        def call_cli(value):
            result = command("cli_actor.py", value=value)
            surface_calls.append({"surface": "CLI", "exitCode": 0, "inputRoot": content_root(value),
                                  "outputRoot": content_root(result)})
            return result

        providers = {"native": SurfaceProvider("native", describe_native, call_native),
                     "http": SurfaceProvider("http", describe_http, call_http),
                     "cli": SurfaceProvider("cli", describe_cli, call_cli)}
        declarations = {name: provider.describe() for name, provider in providers.items()}
        save("capabilities.json", declarations)
        rows, roots = [], {}
        for name, p, c, value, expected in [
            ("python-http", "native", "http", {"legacy_items": [3, 1, 3, 2]}, {"ordered": [1, 2, 3]}),
            ("http-cli", "http", "cli", {"values": [3, 1, 2]}, {"groups": [[1, 2], [3]]})]:
            begin = time.perf_counter()
            handshake = negotiate_handshake(offer(declarations[p]), offer(declarations[c]))
            assert handshake["payload"]["status"] == "accepted"
            assert handshake["payload"]["sharedCapabilities"] == []
            save(name + "-handshake.json", handshake)
            negotiation = negotiate_session(declarations[p], declarations[c], goal=declarations[c]["payload"]["capabilityId"])
            assert negotiation["outcome"] == "ADAPT", negotiation
            contract = negotiation["contract"]
            result = run_session(contract, value, providers=providers, allow_execution=True)
            assert result["status"] == "PASS", result
            assert result["result"] == expected, result
            assert verify_session_receipt(contract, result, expected_contract_root=contract["contractRoot"],
                                          expected_receipt_root=result["receiptRoot"])
            save(name + "-negotiation.json", negotiation)
            save(name + "-receipt.json", result)
            roots[name] = {"contractRoot": contract["contractRoot"], "receiptRoot": result["receiptRoot"]}
            rows.append({"session": name, "elapsedMs": (time.perf_counter()-begin)*1000,
                         "outcome": negotiation["outcome"], "result": result["result"], "offlineVerification": "PASS"})
        # Actual HTTP 503; then operator chooses a healthy stateless provider and
        # explicitly invokes a fresh run. No hidden retry or claimed rollback.
        contract = negotiate_session(declarations["native"], declarations["http"], goal="sort_sequence")["contract"]
        broken = {**providers, "http": SurfaceProvider("http", lambda: describe_http(failing_port), lambda value: call_http(value, failing_port))}
        failure = run_session(contract, {"legacy_items": [2, 1]}, providers=broken, allow_execution=True)
        assert failure["status"] == "FAIL" and failure["error"]["stage"] == "consumer-call", failure
        save("http-failure.json", failure)
        recovery = run_session(contract, {"legacy_items": [2, 1]}, providers=providers, allow_execution=True)
        assert recovery["status"] == "PASS", recovery
        save("http-recovery.json", recovery)
        save("native-invocation-receipts.json", native_receipts)
        save("surface-calls.json", surface_calls)
        summary = {"format": "opp.cha-session-evidence.v0.1", "status": "PASS",
            "environment": {"python": platform.python_version(), "platform": platform.platform(), "oppModule": opp_path},
            "libraries": {name: importlib.metadata.version(name) for name in ("boltons", "jmespath", "more-itertools", "taowind-opp")},
            "sourceFiles": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob("*.py"))},
            "sessions": rows, "expectedRoots": roots, "artifactSha256": artifacts,
            "totalElapsedMs": (time.perf_counter()-started)*1000,
            "automatic": ["native descriptors/OpenAPI parsing", "CHP without shared business capability IDs",
                          "explicit concept matching", "rename synthesis", "runtime schemas", "drift recheck", "offline receipt verification"],
            "manual": ["three surface wrappers", "field concept/unit assertions", "stateless declaration",
                       "provider registration", "execution consent", "operator-directed recovery"],
            "boundary": "Three real installed third-party libraries, three local interface kinds, one operator/physical host. Wrappers authored here. No independent OPP implementation, production network, trusted time or authority attestation. MCP import tested; MCP execution and gRPC NOT_RUN."}
        save("summary.json", summary)
        print(json.dumps({"status": summary["status"], "sessions": rows, "evidence": str(out)}))
    finally:
        for proc in processes:
            proc.terminate()
            try:
                proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate(timeout=5)


if __name__ == "__main__":
    main()
