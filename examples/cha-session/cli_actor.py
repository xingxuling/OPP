"""An independently shaped JSON stdin/stdout CLI backed by more-itertools."""
import json
import sys
from more_itertools import chunked


if "--describe" in sys.argv:
    numbers = {"type": "array", "items": {"type": "integer"}}
    print(json.dumps({"command": "chunk_pairs", "version": "1", "stdin": {
        "type": "object", "properties": {"entries": numbers}, "required": ["entries"], "additionalProperties": False},
        "stdout": {"type": "object", "properties": {"groups": {"type": "array", "items": numbers}},
                   "required": ["groups"], "additionalProperties": False}}))
else:
    request = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    print(json.dumps({"groups": list(chunked(request["entries"], 2))}))
