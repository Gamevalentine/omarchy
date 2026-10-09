#!/usr/bin/env python3
"""Stage 1E: VM-only harness adaptation for testing the already-built ISO.

Never changes the LUNOR product checkout, main branch, or ISO artifact.
Copies the test branch's shell into the disposable installed guest so tests
measure the patch rather than the stale ShellColor-less shell in ISO #19.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: lunor-1e-vm-harness.py <omarchy-iso-tree>")
path = Path(sys.argv[1]) / "bin/omarchy-iso-test"
s = path.read_text()

def once(old: str, new: str, label: str) -> None:
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"1E harness {label}: expected 1 anchor, got {count}")
    s = s.replace(old, new, 1)

once(
    'ssh_guest() {\n  ssh -i "$SSH_KEY" -p "$SSH_PORT" \\',
    'ssh_guest() {\n  timeout --signal=TERM --kill-after=10s 360s \\\n    ssh -i "$SSH_KEY" -p "$SSH_PORT" \\',
    "SSH timeout",
)

# LUNOR-branded greeters have not contained the upstream tagline since ISO #19.
if s.count("Linux by DHH") != 3:
    raise SystemExit("1E harness greeter text changed; review upstream")
s = s.replace("Linux by DHH", "LUNOR .S")

# Hidden overlays are mapped on a different layer; do not confuse mapped
# surfaces with visible ones in the keyboard-shortcut smoke checks.
once(
    r"[.. | objects | select(.namespace? == $namespace)] | length > 0",
    r'[.[].levels | to_entries[]? | select((.key | tonumber) == 3) | .value[]? | select(.namespace? == $namespace)] | length > 0',
    "visible overlay layer",
)

guest_patch = r'''
apply_lunor_1e_shell() {
  [[ -n $SYNC_DIR && -f $SYNC_DIR/shell/Commons/ShellColor.qml ]] || {
    echo "1E: checked-out source is missing ShellColor.qml" >&2
    return 1
  }
  grep -qxF 'singleton ShellColor 1.0 ShellColor.qml' "$SYNC_DIR/shell/Commons/qmldir" || return 1

  log "1E: uploading patched shell code to disposable installed VM"
  tar -C "$SYNC_DIR" -cf - shell |
    ssh_guest "mkdir -p ~/.local/share/lunor-1e && tar -C ~/.local/share/lunor-1e -xf -"

  # The ISO's installed shell is still the OLD Color singleton. Replace that
  # directory ONLY inside the throwaway VM. Avoid leaving old Color.qml
  # alongside new ShellColor.qml and inadvertently testing mixed sources.
  ssh_guest "echo '$GUEST_PASSWORD' | sudo -S sh -c '
    set -eu
    test -f /usr/share/omarchy/shell/Commons/Color.qml
    test -f /home/$GUEST_USER/.local/share/lunor-1e/shell/Commons/ShellColor.qml
    test ! -e /usr/share/omarchy/shell.lunor-1e-original
    mv /usr/share/omarchy/shell /usr/share/omarchy/shell.lunor-1e-original
    cp -a /home/$GUEST_USER/.local/share/lunor-1e/shell /usr/share/omarchy/shell
    chown -R root:root /usr/share/omarchy/shell
    test -f /usr/share/omarchy/shell/Commons/ShellColor.qml
    test ! -e /usr/share/omarchy/shell/Commons/Color.qml
  '"

  log "1E: restarting live Quickshell against patched installed shell"
  ssh_session "timeout --signal=TERM --kill-after=10s 130s omarchy-restart-shell"
  wait_for_guest_state "1E new shell answers IPC" 60 \
    ssh_session "omarchy-shell shell ping"

  ssh_session "grep -qxF 'singleton ShellColor 1.0 ShellColor.qml' /usr/share/omarchy/shell/Commons/qmldir &&
    test -f /usr/share/omarchy/shell/Commons/ShellColor.qml &&
    test ! -e /usr/share/omarchy/shell/Commons/Color.qml &&
    omarchy-shell shell ping" || return 1

  printf 'LUNOR 1E SHA: patched source ShellColor at /usr/share/omarchy/shell\n' >"$RUN_DIR/lunor-1e-provenance.txt"
  ssh_session "pacman -Q quickshell qt6-base qt6-declarative hyprland" \
    >"$RUN_DIR/lunor-1e-packages.txt" 2>&1 || true
  capture_console "success-1e-patched-shell-desktop"
}
'''
once(
    "acceptance_phase() {\n",
    guest_patch + "\nacceptance_phase() {\n",
    "inject guest shell patch",
)
once(
    "  sync_omarchy\n\n  local status=0",
    "  sync_omarchy\n  apply_lunor_1e_shell\n\n  local status=0",
    "invoke guest patch before smoke checks",
)
once(
    "  log \"Collecting artifacts into $RUN_DIR\"\n",
    "  log \"Collecting artifacts into $RUN_DIR\"\n"
    "  ssh_session \"journalctl --user -t omarchy-shell -n 900 --no-pager\" \\\n"
    "    >\"$RUN_DIR/lunor-1e-shell.log\" 2>&1 || true\n",
    "collect shell logs",
)

# This is deliberately a checked-in audit trail; never silently paper over a
# change to upstream's installer/SSH/session harness.
checks = [
    "apply_lunor_1e_shell",
    "wait_for_screen \"LUNOR .S\" 300",
    "timeout --signal=TERM --kill-after=10s 360s",
    "test ! -e /usr/share/omarchy/shell/Commons/Color.qml",
    "success-1e-patched-shell-desktop",
]
for check in checks:
    if check not in s:
        raise SystemExit(f"1E patch missing postcondition: {check}")
path.write_text(s)
print("LUNOR 1E harness preflight: original ISO, patch injection, screenshot and logs configured")
