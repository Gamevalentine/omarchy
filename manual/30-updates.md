# Updates

LUNOR OS does **not** use the upstream Omarchy update service in this development build.

The old Omarchy package channels, package repository, and distro mirrors are intentionally disconnected so an upstream update cannot overwrite LUNOR OS branding or replace this development tree.

## Current development behavior

- _Update > LUNOR OS_ shows a development-build notice instead of running the upstream updater.
- The update indicator stays hidden because no public LUNOR OS release channel exists yet.
- Stable / RC / edge channel switching is disabled.
- The shipped pacman configuration uses the official Arch Linux geo mirror for the Arch repositories only.
- Firmware updates remain available separately through _Update > Firmware_.

A dedicated LUNOR OS package/update service can be added later without renaming the inherited internal commands.

## Updating Arch packages on a development machine

Direct system upgrades remain guarded because a normal Arch upgrade can change low-level packages underneath this development build.

If you deliberately want to maintain a development machine and understand the recovery implications, the existing guard allows an explicit one-transaction bypass:

```bash
sudo env OMARCHY_ALLOW_DIRECT_PACMAN=1 pacman -Syu
```

Take a snapshot first when available. This bypass updates Arch packages only; it is **not** a LUNOR OS release update and does not install LUNOR migrations or future LUNOR packages.

## Package channels

There is currently one effective LUNOR OS state: **development**.

The internal filenames for stable, RC, and edge pacman profiles are retained for compatibility, but all three LUNOR development profiles point at the official Arch Linux repositories and do not configure the Omarchy package repository.

## Upstream resources

The upstream Omarchy release, mirror, and package infrastructure belongs to Omarchy. LUNOR OS does not present those services as its own update infrastructure.
