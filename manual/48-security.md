# Security

LUNOR OS currently inherits most of its security architecture from upstream Omarchy and Arch Linux. The branding work in this branch does not replace those underlying security mechanisms.

## Current security model

1. **Full-disk encryption** can protect data at rest using LUKS on encrypted installations.
2. **Firewall rules** are inherited from the upstream system configuration. Incoming services such as SSH remain opt-in.
3. **Arch Linux packages** provide the underlying rolling package base.
4. **Security-related setup tools** such as fingerprint, FIDO2, SSH, and temporary passwordless sudo keep their inherited technical command names for compatibility.

## Update caveat for this development build

The upstream Omarchy updater and package channels are intentionally disconnected from LUNOR OS.

That prevents an upstream distro update from replacing LUNOR-specific branding, but it also means this development branch does not yet have a first-party LUNOR OS security-update channel. Development machines therefore require deliberate package maintenance until a LUNOR-owned updater exists.

See [Updates](30-updates.md) for the current development policy.

## Changing passwords

On an encrypted install, the drive-unlock password and the user/sudo password are separate. They can still be managed from _Update > Password_ using the inherited system tools.

## Passing on a machine

_Setup > Reset Computer_ retains the inherited factory-reset workflow on supported Btrfs installations. Treat deletion on an unencrypted drive as deletion rather than guaranteed secure erasure.

## Passwordless sudo

The temporary passwordless-sudo feature remains powerful by design. While enabled, processes running as your user may be able to perform privileged actions without an additional password prompt. Use it only when you understand that risk.

## Signing keys and infrastructure

LUNOR OS does **not** currently publish an independent ISO signing key, package-signing key, package repository, mirror network, or CDN.

Keys, signatures, package repositories, ISO URLs, security contacts, and infrastructure under `omarchy.org` authenticate or support **upstream Omarchy**, not LUNOR OS. They must not be represented as LUNOR-owned infrastructure.

A public LUNOR OS release should define its own signing and distribution process before release artifacts are distributed.
