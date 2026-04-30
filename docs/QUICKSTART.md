# Quickstart

Use this workflow the first time you launch Lucid Net.

## 1. Launch

Start the app from the installer shortcut or `LucidNet.exe`. Accept the administrator prompt. A second copy will not start; the existing tray instance remains the active app.

## 2. Check Dashboard

Open Dashboard and confirm:

- active interface;
- current DNS servers;
- gateway;
- proxy state;
- public IP;
- monitor health;
- last DDNS result.

Dashboard quick actions use the currently selected DNS profile from the DNS panel.

## 3. Manage DNS

Open DNS.

1. Leave Interface on Auto unless you need a specific adapter.
2. Select a DNS profile.
3. Click Apply DNS.
4. Use Set to Auto to return the selected adapter to automatic DNS.

To add your own DNS profile, enter a name and comma-separated IPv4/IPv6 addresses in Custom DNS profile, then save. Saving an existing name overwrites that profile. Delete profile removes the selected profile.

## 4. Manage Proxy

Open Proxy.

1. Select a saved `host:port` proxy profile.
2. Enable or disable the current user's Windows proxy setting.
3. Add or delete proxy profiles as needed.

The app preserves existing proxy bypass and PAC values in restore snapshots.

## 5. Configure DDNS

Open DDNS.

1. Paste your provider's update URL.
2. Save it.
3. Use Force sync DDNS to test it.
4. Enable Auto-update DDNS in Settings only after the URL is saved.

Clearing the URL disables Auto-DDNS. Failed automatic updates are retried with backoff until the current public IP is successfully synced.

## 6. Recover

If a DNS or proxy change breaks connectivity, use Dashboard -> Restore. Restore points are updated only after successful app-driven changes, so a failed operation does not destroy the previous usable restore point.

## 7. Support Bundle

Use Tools -> Copy diagnostics or Export diagnostics before asking for help. Diagnostics redact DDNS paths/query values, common secret fields, proxy credentials, and plugin event details where possible.
