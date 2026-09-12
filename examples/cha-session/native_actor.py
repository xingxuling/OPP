"""A Boltons-backed Python actor. No OPP imports or shared business schema."""
import json
import sys
from boltons.iterutils import unique


def unique_numbers(legacy_items: list) -> dict:
    return {"unique_items": unique(legacy_items)}


if __name__ == "__main__":
    numbers = {"type": "array", "items": {"type": "integer"}}
    def schema(field):
        return {"type": "object", "properties": {field: numbers}, "required": [field], "additionalProperties": False}
    print(json.dumps({"name": "unique_numbers", "revision": "1",
                      "input": schema("legacy_items"), "output": schema("unique_items")}))
