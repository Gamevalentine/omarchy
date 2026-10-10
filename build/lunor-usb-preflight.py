#!/usr/bin/env python3
"""Fast offline safety checks for the LUNOR USB feasibility laboratory.

This is a guardrail, not a proof that a disk image is safe to publish.
Never use the lab base.qcow2 or raw conversion as an end-user image.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
workflow = (ROOT / ".github/workflows/lunor-usb-image-lab.yml").read_text()
probe = (ROOT / "build/lunor-usb-image-lab.sh").read_text()
docs = (ROOT / "docs/usb-image-lab.md").read_text()
errors = []


def check(ok: bool, description: str) -> None:
    if not ok:
        errors.append(description)


# The expensive install job should run only with an explicit human trigger.
check(bool(re.search(r"(?m)^  workflow_dispatch:\s*$", workflow)), "Manual trigger missing")
check(not re.search(r"(?m)^  (push|pull_request|schedule):", workflow),
      "An automatic expensive-workflow trigger was introduced")
check("timeout-minutes: 40" in workflow and "timeout-minutes: 35" in workflow,
      "Hard GitHub Actions timeout was removed")
check("trap cleanup EXIT" in workflow and "docker rm -f" in workflow,
      "Container cleanup protection was removed")

# A prior successful run used an already-verified ISO, not a moving URL.
check("37935766465" in workflow and "sha256sum -c release/*.sha256" in workflow,
      "Verified ISO provenance/checksum guard missing")
check('4f4b3e3da9214da2e1625b3de935745148d16fbc' in workflow,
      "Upstream omarchy-iso commit pin missing")

# Only a deliberately small diagnostics allowlist may leave the runner.
artifact = workflow.split("uses: actions/upload-artifact@", 1)
check(len(artifact) == 2, "Missing QA report upload definition")
if len(artifact) == 2:
    tail = artifact[1]
    glob_lines = re.findall(r"(?m)^\s+lunor-source/usb-image-lab-report/\*\.[^\s]+$", tail)
    expected = {
        "lunor-source/usb-image-lab-report/*.txt",
        "lunor-source/usb-image-lab-report/*.json",
    }
    check({line.strip() for line in glob_lines} == expected,
          "Unexpected QA artifact type; binary/test disk must never be uploaded")
    check(not re.search(r"(?m)^\s+.*(?:base\.qcow2|\*\.img|\*\.raw|\*\.log|\*\.qcow2)\s*$", tail),
          "Disk image or raw log added to published artifacts")

check("id_ed25519" in probe and "DO NOT DISTRIBUTE" in probe,
      "Test-credential warning/guard missing")
check('."virtual-size"' in probe and 'BOOTX64.EFI' in probe,
      "Disk-size or UEFI fallback check was removed")
check("usb-storage" in probe and "fresh-nvram.fd" in probe,
      "USB device / independent firmware boot probe was removed")
check("Status: **experimental**" in docs,
      "Lab must remain explicitly experimental")

if errors:
    for error in errors:
        print("FAIL:", error, file=sys.stderr)
    sys.exit(1)
print("PASS: USB lab static safety guardrails present.")
print("NOTE: This does not authorize publishing a user disk image.")
