"""Run from ANY cwd with an installed OPP wheel, not an editable/source import.

python /checkout/scripts/verify_external_projects.py --out /new/evidence
Dependencies: examples/external-projects/requirements.txt. No install or network
is performed by this command. Every output directory must be new.
"""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
import time
from pathlib import Path

import opp
from opp.sdk import (SemanticPort, InvocationSpec, synthesize_bridge, run_interop,
                     verify_interop_result, verify_repository_semantics, content_root)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def installed_source(name, module):
    dist = importlib.metadata.distribution(name)
    root = Path(importlib.util.find_spec(module).origin).parent
    files = []
    for f in sorted(dist.files or [], key=str):
        if str(f).endswith('.pyc') or '__pycache__' in str(f):
            continue
        p = Path(dist.locate_file(f))
        if p.is_file():
            files.append({'path': str(f).replace('\\', '/'), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    return root, {'distribution': name, 'version': dist.version, 'files': files,
                  'manifestRoot': content_root(files), 'metadataLicense': dist.metadata.get('License-Expression') or dist.metadata.get('License'),
                  'projectUrls': dist.metadata.get_all('Project-URL') or []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    home = Path(__file__).resolve().parents[1]
    adapter = home / 'examples/external-projects/adapters.py'
    (out / 'adapters.py').write_bytes(adapter.read_bytes())
    # Retain the exact reviewed adapter used in each run for external replay.
    distributions = [('boltons', 'boltons'), ('more-itertools', 'more_itertools'), ('jmespath', 'jmespath')]
    scans = {}
    for name, module in distributions:
        started = time.perf_counter()
        root, source = installed_source(name, module)
        report = verify_repository_semantics(root, source_id=name)
        save(out / f'{name}-source.json', source)
        save(out / f'{name}-discovery.json', report.to_dict())
        scans[name] = {'interfaceCount': len(report.interfaces),
            'untypedOutputs': sum(not p.shape for i in report.interfaces for p in i.outputs),
            'scanSeconds': round(time.perf_counter() - started, 4), 'version': source['version']}
    item_shape = {'type': 'array', 'items': {'type': 'string'}}
    def port(name, field, direction):
        return SemanticPort(name, name, direction, {'type': 'object', 'properties': {field: item_shape},
                            'required': [field], 'additionalProperties': False}, confidence=.99)
    # These shapes are manually declared. OPP synthesizes only the normalized
    # item_list -> itemList field rename; it does not infer library semantics.
    plan = synthesize_bridge(port('producer.items', 'item_list', 'output'), port('consumer.items', 'itemList', 'input'))
    payload = {'items': ['香港🌏', 'B', '香港🌏', 'A']}
    cases = [
        ('boltons', 'boltons_producer', 'consume_more', {'chunks': [['香港🌏', 'B'], ['A']]}),
        ('more-itertools', 'more_producer', 'consume_jmespath', {'values': ['A', 'B', '香港🌏']}),
        ('jmespath', 'jmespath_producer', 'consume_boltons', {'values': ['A', 'B', '香港🌏']}),
    ]
    rows = []
    for name, producer, consumer, expected in cases:
        started = time.perf_counter()
        def invocation(function):
            return InvocationSpec(function, 'python-function', str(out), f'adapters.py:{function}').to_dict()
        spec = {'format': 'taowind.opp.interop-run.v0.1', 'runId': name, 'producer': invocation(producer),
                'consumer': invocation(consumer), 'bridgePlan': plan}
        result = run_interop(spec, payload, allow_execution=True)
        verified = verify_interop_result(result, spec, payload)
        if result['result'] != expected:
            raise RuntimeError(f'EXTERNAL_RESULT_MISMATCH:{name}')
        negative_input = {'items': 7}
        negative = run_interop(spec, negative_input, allow_execution=True)
        if negative['receipt']['status'] != 'FAIL' or negative['consumer'] is not None:
            raise RuntimeError(f'INVALID_INPUT_ACCEPTED:{name}')
        recovered = run_interop(spec, payload, allow_execution=True)
        verify_interop_result(recovered, spec, payload)
        if recovered['result'] != expected:
            raise RuntimeError(f'RECOVERY_MISMATCH:{name}')
        record = {'project': name, 'runSpec': spec, 'input': payload, 'expected': expected,
            'result': result, 'negativeInput': negative_input, 'negative': negative, 'recovered': recovered}
        save(out / f'{name}-run.json', record)
        rows.append({'project': name, **scans[name], 'automatedRunSeconds': round(time.perf_counter()-started, 4),
            'humanMinutes': None, 'humanTimingStatus': 'NOT_MEASURED',
            'manualInterventions': ['choose API', 'write thin library wrapper', 'declare JSON field schema', 'install pinned packages'],
            'automatic': ['static signature discovery', 'declared-shape compatibility', 'normalized field-rename synthesis', 'child execution receipts'],
            'bridge': result['receipt']['status'], 'negative': negative['producer']['receipt']['error'],
            'recovery': 'EXPLICIT_STATELESS_REINVOKE', 'offlineVerified': verified,
            'independentOperator': False, 'physicalMultiHost': 'NOT_RUN'})
    artifacts = [{'path': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(out.iterdir()) if p.is_file()]
    summary = {'status': 'REAL_THIRD_PARTY_LIBRARIES_LOCAL_OPERATOR', 'python': platform.python_version(),
        'oppImportPath': opp.__file__, 'executable': sys.executable, 'cases': rows, 'artifacts': artifacts,
        'artifactRoot': content_root(artifacts), 'boundary': 'Real installed library execution with human-authored adapters; no independent consumer acceptance, physical devices, authority or production claim. Timings exclude install and authoring.'}
    save(out / 'summary.json', summary)
    print(json.dumps({'status': summary['status'], 'out': str(out), 'cases': rows}, ensure_ascii=True))


if __name__ == '__main__':
    main()
