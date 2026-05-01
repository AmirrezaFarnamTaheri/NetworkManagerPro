# Deep Diagnostics Framework

Status: implementation and safety note for R-053 through R-056.

## Safety Model

Deep diagnostics are consent-based. Each active test must explain:

- What will be tested.
- Whether the test is passive, local active, or external active.
- Approximate duration.
- Data collected.
- How cancellation works.
- How results are interpreted.

Results separate evidence from recommendations. Findings should describe what was observed, assign confidence, and avoid attribution claims.

## Implemented Scaffolding

`deep_diagnostics.py` defines:

- Consent prompts for captive portal, DNS integrity, and TLS inspection checks.
- Versioned result schema.
- Captive portal diagnostics using the existing safe connectivity endpoint classifier.
- DNS integrity classification from local versus user-approved trusted resolver answers.
- TLS certificate issuer evidence classification.
- A Cloudflare DoH JSON resolver helper for user-consented DNS comparison.
- Frontier capability gating through `frontier_policy.py` for research-grade diagnostics and prototypes.

The module is testable with injected resolvers, fetchers, and certificate providers. This keeps automated tests local and avoids embedding restricted target lists.

The CLI exposes consent-gated entry points:

```powershell
python lucid_cli.py diagnose captive --i-consent --json
python lucid_cli.py diagnose dns --domain example.com --i-consent --json
python lucid_cli.py diagnose tls --host example.com --i-consent --json
python lucid_cli.py frontier catalog --json
python lucid_cli.py frontier status --json
```

Unimplemented research and frontier work is consolidated in `docs/RESEARCH_AND_FRONTIER_BACKLOG.md`.

## DNS Integrity

The DNS diagnostic compares answers for a benign user-approved domain. It can classify:

- `normal`: local and trusted answers match.
- `filtered`: local resolver returns no answer while trusted resolver returns one.
- `mismatch`: local and trusted answers differ completely.
- `partial_mismatch`: answers overlap but differ.
- `inconclusive`: neither side gives useful evidence.

This is troubleshooting evidence, not proof of malicious intent.

## TLS And SNI

TLS inspection diagnostics collect certificate issuer and subject evidence for benign endpoints. Expected issuer hints may be provided for controlled tests. SNI filtering research must use owned or benign test domains only and must not embed blocked-site lists.

## Captive Portal And HTTP Proxy

Captive portal diagnostics reuse the safe endpoint classifier:

- Expected response means normal HTTP connectivity.
- Redirect suggests captive portal sign-in.
- Modified content suggests captive portal or transparent HTTP modification.
- Failed check remains inconclusive.

## Boundaries

Lucid Net may diagnose network behavior and recommend lawful, user-consented local configuration changes. Features involving policy bypass, traffic camouflage, identity rotation, or anti-censorship countermeasures require legal, ethical, safety, and feasibility review before implementation.
