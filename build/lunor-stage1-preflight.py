#!/usr/bin/env python3
"""LUNOR Stage 1: quick repository-only safety preflight.

No QEMU, no ISO download, no disk access outside this checkout.
This does not prove that installed Linux boots or that web testing works.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
findings = []

def require(path, *needles):
    file = ROOT / path
    if not file.is_file():
        findings.append(f"MISSING: {path}")
        return
    content = file.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in content:
            findings.append(f"CHECK: {path} lacks {needle!r}")

# Source identity and ISO creation controls.
require("README.md", "# LUNOR OS", "Internal compatibility names")
require(".github/workflows/lunor-iso-build-test.yml",
        "omarchy-iso-make", "lunor-stage-a-overlay.py",
        "sha256sum", "retention-days: 7",
        "vm-test:", "--no-preview")
require("build/lunor-stage-a-overlay.py",
        "omarchy_prompt_login_mode",
        "user_autologin.txt", "defer_provisioning")
# Boot/kernel and desktop initialization path.
require("etc/limine-entry-tool.d/omarchy-defaults.conf",
        'TARGET_OS_NAME="LUNOR OS"', "ENABLE_LIMINE_FALLBACK=yes")
require("etc/limine-entry-tool.d/omarchy-uki.conf",
        "ENABLE_UKI=yes")
require("etc/mkinitcpio.conf.d/omarchy_hooks.conf",
        "autodetect", "block", "filesystems")
require("etc/sddm.conf.d/10-wayland.conf",
        "DisplayServer=wayland", "start-hyprland")
require("install/config/enable-services.sh", "sddm.service")
require("config/hypr/hyprland.lua",
        "default.hypr.omarchy", "default.hypr.toggles")
require("default/hypr/autostart.lua", "omarchy-launch-shell")
require("install/provisioning/omarchy-provision-owner.service",
        "ConditionPathExists=/var/lib/omarchy/provisioning/pending")
require("bin/omarchy-provision-owner",
        "PROVISIONING_DIR=/var/lib/omarchy/provisioning")

if findings:
    print("STAGE 1 STATIC PRE-FLIGHT: BLOCKED", file=sys.stderr)
    for issue in findings:
        print(" -", issue, file=sys.stderr)
    sys.exit(1)

print("STAGE 1 STATIC PRE-FLIGHT: PASS (source invariants only)")
print("NO APPROVAL is implied for distributing QCOW2, testing physical hardware,")
print("or claiming browser control of Hyprland. See docs/LUNOR_GIAI_DOAN_1_RASOAT.md")
