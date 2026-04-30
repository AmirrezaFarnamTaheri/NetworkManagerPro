# Plugin Signing Research

Status: research recommendation for the v1 trusted-only plugin roadmap.

## Goal

Signed plugins should let Network Manager Pro verify publisher identity and bundle integrity before installation or update. Signing does not replace sandboxing; it reduces supply-chain risk for trusted plugins.

## Recommended Direction

Use signed plugin bundles as the first implementation target:

- Package each plugin as a zip bundle with `plugin.json`, code, assets, and a detached signature file.
- Include a manifest digest in the signed payload.
- Verify the signature before extracting or enabling the plugin.
- Pin trusted publisher identities in the marketplace or local trust store.
- Reject unsigned, tampered, expired, or revoked bundles by default.

## Options Considered

- PGP: mature and offline-friendly, but user key management can be confusing.
- sigstore: strong modern supply-chain story, but online verification and Windows desktop UX need more design.
- Authenticode: familiar on Windows, but less natural for individual plugin bundles.
- Repository-pinned signatures: simple for a first-party registry, but weaker for a broader marketplace.

## Open Questions

- Which trust root owns first-party plugins?
- How are publisher keys rotated or revoked?
- Can enterprise policy pin an internal publisher?
- Should unsigned local-development plugins require a visible development mode?

## Prototype Acceptance Criteria

- A signed sample bundle installs successfully.
- A tampered bundle is rejected before extraction.
- A revoked or unknown publisher is rejected.
- The UI explains signature status before enabling a plugin.
