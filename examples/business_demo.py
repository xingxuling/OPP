from __future__ import annotations

import json
from opp.integrity import content_root
from opp.runtime import run_interop


def invocation(spec_id: str, entrypoint: str) -> dict:
    return {
        "format": "taowind.opp.invocation-spec.v0.1",
        "version": "0.3.0-candidate.1",
        "adapterKind": "python-function",
        "sourceRoot": ".",
        "entrypoint": entrypoint,
        "callingConvention": "kwargs",
        "timeoutMs": 3000,
        "maxOutputBytes": 262144,
        "cwdPolicy": "ephemeral",
        "environmentPolicy": "sanitized",
        "authorityRequired": [],
        "status": "candidate",
        "specId": spec_id,
    }


operations = [
    {"op": "rename", "from": "name", "to": "customer_name"},
    {"op": "rename", "from": "service", "to": "service_code"},
    {"op": "rename", "from": "slot", "to": "preferred_time"},
    {"op": "inject-default", "field": "channel", "value": "legacy-web-form"},
    {
        "op": "select",
        "fields": [
            "customer_name",
            "phone",
            "service_code",
            "preferred_time",
            "notes",
            "channel",
        ],
    },
]

bridge_body = {
    "format": "taowind.opp.auto-bridge-plan.v0.1",
    "version": "0.2.0-candidate.1",
    "bridgeId": "business-demo-booking-to-crm",
    "status": "candidate",
    "producerPort": "legacy.booking.request",
    "consumerPort": "crm.lead.create",
    "operations": operations,
    "executionModel": "opp-declarative-json-transform",
    "authority": {"required": [], "available": [], "promotionPerformed": False},
    "safety": {
        "sourceCodeExecution": False,
        "arbitraryCodeGeneration": False,
        "informationInvention": False,
        "authorityInvention": False,
        "lossyAllowed": True,
    },
    "boundary": "Demo-only field mapping. No real CRM or booking system is contacted.",
}
bridge_plan = {**bridge_body, "planRoot": content_root(bridge_body)}

run_spec = {
    "format": "taowind.opp.interop-run.v0.1",
    "version": "0.3.0-candidate.1",
    "runId": "business-demo-booking-to-crm",
    "producer": invocation(
        "business-demo-booking-intake",
        "examples/business-fixtures/intake.py:collect_booking_request",
    ),
    "bridgePlan": bridge_plan,
    "consumer": invocation(
        "business-demo-crm",
        "examples/business-fixtures/crm.py:create_crm_lead",
    ),
    "status": "candidate",
}

producer_input = {
    "name": "陈小姐",
    "phone": "+852 6123 4567",
    "service": "physio-first-visit",
    "slot": "2026-09-15 14:30",
    "notes": "希望安排下午时段",
}

result = run_interop(run_spec, producer_input, allow_execution=True)

summary = {
    "场景": "旧预约表单 -> 新 CRM 线索",
    "说明": "这是本地演示，不连接真实预约系统或 CRM。重点是字段差异如何被显式转换并留下回执。",
    "原始输入": producer_input,
    "旧系统输出": result.get("producer", {}).get("result"),
    "OPP 转换后": result.get("transformed"),
    "新系统结果": result.get("result"),
    "状态": result.get("receipt", {}).get("status"),
    "回执根": result.get("receipt", {}).get("receiptRoot"),
}

print(json.dumps(summary, ensure_ascii=False, indent=2))
