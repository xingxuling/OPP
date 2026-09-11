# Third-party GitHub REST fixture

This is a manual, read-only candidate fixture for the OPP third-party
interoperability frontier. It calls the public GitHub REST repository endpoint
with an explicit `GET`, passes the selected response through an OPP declarative
identity bridge, and invokes a local consumer.

It is not a general HTTP adapter, not a production sandbox, and not part of the
default unit-test suite. Run it only with explicit execution consent and record
the returned receipt as time-bound evidence.

On the 2026-09-11 Windows audit host, the parent host could fetch the endpoint,
but the OPP child failed closed with `GITHUB_NETWORK_ERROR:gaierror` because
the sanitized child environment does not implicitly inherit the host proxy or
network configuration. That negative result is intentional evidence, not a
third-party interoperability PASS.
