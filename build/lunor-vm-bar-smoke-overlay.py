#!/usr/bin/env python3
"""Patch only the disposable VM test harness, never an ISO artifact.

The current released ISO must remain immutable while a candidate Bar.qml fix
is tested. Copy that one candidate source file into the throwaway VM after
the ordinary test-suite sync, restart the shell, and run full acceptance.
A successful VM-only test is NOT evidence the existing ISO contains the fix.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: lunor-vm-bar-smoke-overlay.py <harness-path>")

harness = Path(sys.argv[1])
source = harness.read_text()
old = """  establish_session
  sync_omarchy

  local status=0
  shortcut_smoke_phase || status=1
"""
new = """  establish_session
  sync_omarchy

  # LUNOR QA ONLY: validate the candidate bar fix inside this disposable VM.
  # The artifact ISO remains unchanged; never apply this during a full build.
  log "LUNOR QA: overlaying candidate Bar.qml into disposable VM"
  tar -C "$SYNC_DIR" -cf - shell/plugins/bar/Bar.qml |
    ssh_guest "mkdir -p .local/share/omarchy && tar -C .local/share/omarchy -xf -"
  ssh_guest "printf '%s\\n' '$GUEST_PASSWORD' | sudo -S install -m 0644 .local/share/omarchy/shell/plugins/bar/Bar.qml /usr/share/omarchy/shell/plugins/bar/Bar.qml"
  ssh_guest "omarchy-restart-shell"
  ssh_guest "omarchy-shell shell ping"

  local status=0
  shortcut_smoke_phase || status=1
"""

if source.count(old) != 1:
    raise SystemExit("Upstream VM acceptance entrypoint changed; refuse to patch")
harness.write_text(source.replace(old, new, 1))
