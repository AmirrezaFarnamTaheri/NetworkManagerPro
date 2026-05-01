# Changelog

## Unreleased

- Store runtime config and user plugins under `%LOCALAPPDATA%\LucidNet`.
- Create config from built-in defaults instead of requiring a loose example config file.
- Build a PyInstaller onefile executable and wrap it in one installer executable.
- Add DNS/proxy profile deletion for user-managed predefined lists.
- Default DDNS automation to off until a provider URL is configured.
- Reject unsafe proxy profile formats and preserve proxy bypass/PAC settings during restore.
- Retry DDNS updates until the current public IP is successfully synced.
- Dispatch tray UI actions through the Tk main thread.
- Add a single-instance guard.
- Enforce v1 plugin API permissions and stop plugin tasks on partial load failure.
- Redact diagnostics/history more aggressively.
- Clean and verify release build output.
- Add a consolidated research/frontier backlog and queryable frontier capability gates for CLI, GUI, and diagnostics.
