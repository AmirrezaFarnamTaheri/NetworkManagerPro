# Overlay And Frontier Research

Status: research and safety note for R-065, R-066, R-068, and adjacent frontier ideas.

## Overlay Networks

Overlay orchestration starts read-only. The first supported operations should detect installed Tailscale and ZeroTier clients and collect user-consented status output. Any exit-node, route, or peer-control operation requires explicit consent and vendor CLI/API stability review.

Safe first scope:

- Detect whether supported overlay CLIs are installed.
- Read local status.
- Explain overlay adapter state alongside local adapters.
- Avoid changing routes, peers, or exit-node state.

## Domain-Fronting And Traffic Camouflage

Domain-fronting, traffic camouflage, protocol shaping, and similar ideas remain research questions only. They are not product features and must not be implemented without legal, ethical, safety, feasibility, provider-policy, and abuse-risk review.

Allowed roadmap treatment:

- Preserve the ideas as research history.
- Ask what can be detected safely.
- Ask what can be explained lawfully.
- Ask what requires external expert review.

Disallowed in product docs:

- Operational bypass steps.
- Target lists.
- Provider-specific evasion instructions.
- Hidden or automatic policy circumvention.

## Advanced Anti-Censorship Diagnostics

Advanced concepts such as active probing detection, fingerprinting analysis, forged packet detection, and penalty-box behavior are diagnostics-only research. Any active external test requires owned infrastructure, clear consent, bounded duration, evidence/recommendation separation, and no attribution claims without strong corroboration.

## Safety Boundary

Lucid Net may diagnose network behavior and recommend lawful, user-consented local configuration changes. Features involving policy bypass, traffic camouflage, identity rotation, or anti-censorship countermeasures require legal, ethical, safety, and feasibility review before implementation.
