# LUNOR OS

LUNOR OS is a branded development build based on the upstream [Omarchy](https://omarchy.org/) Linux distribution.

The user-facing product identity in this branch is **LUNOR OS**. Internal compatibility names such as `omarchy-*`, `OMARCHY_PATH`, package names, service IDs, plugin IDs, and configuration paths are intentionally retained where changing them would add risk without changing what the user sees.

Upstream Omarchy remains the source of the underlying system and is credited as such.

## LUNOR OS documentation

These pages describe the LUNOR-specific state of this branch:

- [Welcome to LUNOR OS](manual/01-welcome-to-omarchy.md)
- [Updates](manual/30-updates.md)
- [Branding](manual/41-branding.md)
- [Security](manual/48-security.md)

The rest of the `manual/` directory is inherited upstream documentation and has not yet been fully rewritten as LUNOR documentation. Use it as a technical compatibility reference rather than as a statement that upstream services, releases, package infrastructure, or support channels belong to LUNOR OS.

For the authoritative upstream documentation, use the [Omarchy manual](https://omarchy.org/manual/).

## Development status

This branch currently focuses on:

- LUNOR OS boot, login, desktop, menu, About, setup, and wallpaper branding.
- Preserving stable upstream technical identifiers internally.
- Disconnecting upstream Omarchy update/package channels until LUNOR OS has its own update infrastructure.
- Keeping upstream attribution explicit rather than presenting upstream services as LUNOR-owned.

## License

This project retains the upstream MIT licensing terms. LUNOR OS branding changes do not remove upstream attribution or licensing obligations.
