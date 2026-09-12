"""Import surface declarations into RCP; transport and trust remain provider-owned."""
from copy import deepcopy

from .capability import _payload
from .integrity import content_root, seal_envelope

SESSION_PROFILE = "opp.session.v0.1"


def describe_surface(*, participant, capability_id, input_schema, output_schema,
                     surface, semantics, authority_required=(),
                     side_effects=(), statefulness="unknown"):
    """Create an RCP declaration, with explicit caller-supplied semantic evidence.

    Surface must include kind, bindingId, revision and discoveryRoot. No command,
    endpoint or capability description is executed by this importer.
    """
    for key in ("kind", "bindingId", "revision", "discoveryRoot"):
        if not isinstance(surface.get(key), str) or not surface[key]:
            raise ValueError(f"SURFACE_FIELD_REQUIRED:{key}")
    declaration = seal_envelope({
        "format": "taowind.opp.reality-envelope.v0.1",
        "protocol": "opp.rcp.v0.1", "version": "0.1.0-candidate.1",
        "kind": "capability", "id": f"rcp:{participant}:{capability_id}",
        "status": "candidate", "issuedAt": "1970-01-01T00:00:00Z",
        "issuer": {"id": participant, "type": "service"},
        "payload": {
            "capabilityId": capability_id, "name": capability_id,
            "domain": "surface-provider", "operation": capability_id,
            "inputModalities": ["json"], "outputModalities": ["json"],
            "inputSchema": deepcopy(input_schema), "outputSchema": deepcopy(output_schema),
            "determinism": "unknown", "statefulness": statefulness,
            "authorityRequired": list(authority_required), "sideEffects": list(side_effects),
            "reversibility": "unknown", "availability": "candidate-only",
            "evidence": [surface["discoveryRoot"]],
            "claimBoundary": "Provider declarations and semantic assertions, not authenticated facts.",
        },
        "extensions": {"session": {"profile": SESSION_PROFILE,
            "surface": deepcopy(surface), "semantics": deepcopy(semantics)}},
    })
    _payload(declaration, "surface")
    return declaration


def describe_openapi(document, *, path, method="post", response_status="200", **kwargs):
    """Bounded OpenAPI 3.1 JSON-body operation importer; no network/ref resolution.

    Parameters, security, callbacks, links and multiple success bodies require a
    richer provider. Ref-containing schemas remain unexecutable in this profile.
    """
    if not str(document.get("openapi", "")).startswith("3.1."):
        raise ValueError("OPENAPI_VERSION_UNSUPPORTED")
    item = document["paths"][path]
    operation = item[method.lower()]
    if (document.get("security") or item.get("parameters") or
            operation.get("parameters") or operation.get("security") or
            operation.get("callbacks") or "$ref" in item):
        raise ValueError("OPENAPI_POLICY_OR_PARAMETERS_UNSUPPORTED")
    successes = [k for k in operation["responses"] if str(k).startswith("2")]
    if successes != [response_status]:
        raise ValueError("OPENAPI_SUCCESS_VARIANTS_UNSUPPORTED")
    response = operation["responses"][response_status]
    request = operation["requestBody"]
    if response.get("links") or request.get("required") is not True:
        raise ValueError("OPENAPI_LINKS_OR_OPTIONAL_BODY_UNSUPPORTED")
    if (set(request["content"]) != {"application/json"} or
            set(response["content"]) != {"application/json"}):
        raise ValueError("OPENAPI_MEDIA_TYPE_UNSUPPORTED")
    surface = {**kwargs.pop("surface"), "kind": "openapi-json",
               "discoveryRoot": content_root(document), "path": path,
               "method": method.lower(), "responseStatus": response_status}
    return describe_surface(capability_id=operation["operationId"],
        input_schema=request["content"]["application/json"]["schema"],
        output_schema=response["content"]["application/json"]["schema"],
        surface=surface, **kwargs)


def describe_mcp_tool(tool, **kwargs):
    """Import one tools/list declaration; absent output schema stays unknown.

    MCP annotations are hints, never authority or proof of side-effect freedom.
    A provider must treat isError as failure and return structuredContent.
    """
    surface = {**kwargs.pop("surface"), "kind": "mcp-tool",
               "discoveryRoot": content_root(tool), "toolName": tool["name"]}
    return describe_surface(capability_id=tool["name"], input_schema=tool["inputSchema"],
        output_schema=tool.get("outputSchema"), surface=surface, **kwargs)
