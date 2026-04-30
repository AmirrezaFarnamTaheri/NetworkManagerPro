# Security Policy

Lucid Net is a Windows desktop utility that can run elevated and change local DNS, proxy, and startup settings. Treat configuration files and plugins as sensitive local data.

## Reporting

Report security issues privately to the project maintainer. Include:

- affected version or commit;
- reproduction steps;
- whether the issue requires administrator rights;
- any logs or diagnostics, with private tokens redacted.

## Plugin Trust

Plugins run in-process with the same OS privileges as the app. Manifest permissions gate the app's plugin API, but they are not a sandbox. Only install plugins from sources you trust.

## Diagnostics

Diagnostics redact configured DDNS URL paths/query values, common secret fields, proxy credentials, and plugin-provided event details where possible. Review bundles before sharing them outside your machine.

## License

Lucid Net is distributed under AGPL-3.0-only. Security reports should still be sent privately before public disclosure.
