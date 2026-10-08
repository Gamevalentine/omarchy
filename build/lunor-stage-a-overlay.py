#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: lunor-stage-a-overlay.py <omarchy-iso-dir>")

iso = Path(sys.argv[1])


def replace_once(rel: str, old: str, new: str, label: str) -> None:
    p = iso / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match in {rel}, found {count}")
    p.write_text(s.replace(old, new, 1))


p = iso / "configs/airootfs/root/configurator"
s = p.read_text()

source_line = 'source "$DISK_PARTITIONING"\n'
if s.count(source_line) != 1:
    raise SystemExit("Stage A defaults: disk helper source line changed upstream")
s = s.replace(
    source_line,
    source_line
    + '\n# LUNOR Stage A defaults. The user can override both in the wizard.\n'
      'auto_login=true\n'
      'login_mode_label="Automatic login"\n',
    1,
)

user_tail = '''  omarchy_prompt_identity || return $?
  omarchy_prompt_hostname || return $?
  omarchy_prompt_timezone || return $?
}'''
user_tail_new = '''  omarchy_prompt_identity || return $?
  omarchy_prompt_hostname || return $?
  omarchy_prompt_timezone || return $?
  omarchy_prompt_login_mode || return $?
}'''
if s.count(user_tail) != 1:
    raise SystemExit("Stage A login choice: user form changed upstream")
s = s.replace(user_tail, user_tail_new, 1)

review_old = '''Hostname,$hostname
Timezone,$timezone
Keyboard,$keyboard" |'''
review_new = '''Hostname,$hostname
Timezone,$timezone
Keyboard,$keyboard
Desktop login,$login_mode_label" |'''
if s.count(review_old) != 1:
    raise SystemExit("Stage A login review: table changed upstream")
s = s.replace(review_old, review_new, 1)

write_old = '''  printf '%s\\n' "$encrypt_installation" >user_encrypt_installation.txt

  if $defer_provisioning; then'''
write_new = '''  printf '%s\\n' "$encrypt_installation" >user_encrypt_installation.txt
  printf '%s\\n' "$auto_login" >user_autologin.txt

  if $defer_provisioning; then'''
if s.count(write_old) != 1:
    raise SystemExit("Stage A autologin state: write_user_files changed upstream")
s = s.replace(write_old, write_new, 1)

dry_old = '''  echo -e "\\nDisk Encryption:"
  cat user_encrypt_installation.txt

  rm -f user_configuration.json user_credentials.json user_full_name.txt user_email_address.txt user_encrypt_installation.txt
}'''
dry_new = '''  echo -e "\\nDisk Encryption:"
  cat user_encrypt_installation.txt

  echo -e "\\nAutomatic Login:"
  cat user_autologin.txt

  rm -f user_configuration.json user_credentials.json user_full_name.txt user_email_address.txt user_encrypt_installation.txt user_autologin.txt
}'''
if s.count(dry_old) != 1:
    raise SystemExit("Stage A autologin dry-run output changed upstream")
s = s.replace(dry_old, dry_new, 1)

anchor = '''# Decide half of the free-space install: checks, free-space analysis, and the
# encryption confirm. Sets the globals run_partition_execute needs. Returns 1
# to fall back to the install-mode picker.
'''
helper = '''choose_disk_security() {
  local choice status

  choice=$(printf '%s\\n' \\
    "No disk encryption (boot without LUKS password)" \\
    "Encrypt disk with password (LUKS)" \\
    "Back" | \\
    gum choose --height 3 --selected "No disk encryption (boot without LUKS password)" --header "Disk security") && status=0 || status=$?
  ((status == 0)) || return $status

  case "$choice" in
    "No disk encryption (boot without LUKS password)") encrypt_installation=false ;;
    "Encrypt disk with password (LUKS)") encrypt_installation=true ;;
    "Back") return 1 ;;
  esac
}

'''
if s.count(anchor) != 1:
    raise SystemExit("Stage A disk security: helper anchor changed upstream")
s = s.replace(anchor, helper + anchor, 1)

free_old = '''  # Default to encrypted and hide the unencrypted path behind Ctrl+C,
  # matching the full-disk flow. The dedicated Omarchy ESP always supports
  # LUKS, so encryption is always on the table here.
  local mode="encrypted" affirmative confirm_status

  while true; do
    clear_logo
    echo
    say "Install Omarchy in the $(to_gb $INSTALL_MAX_B) of free space."

    case $mode in
      encrypted)
        say --foreground 8 "Press Ctrl+C for unencrypted install."
        affirmative="Yes, install"
        ;;
      unencrypted)
        affirmative="Yes, install without encryption"
        ;;
    esac
    echo

    gum confirm --affirmative "$affirmative" --negative "No, change it" \\
      "Confirm installing on $disk"
    confirm_status=$?

    case $confirm_status in
      0)
        [[ $mode == "encrypted" ]] && encrypt_installation=true || encrypt_installation=false
        break
        ;;
      1)
        return 1
        ;;
      130)
        case $mode in
          encrypted) mode="unencrypted" ;;
          unencrypted) mode="encrypted" ;;
        esac
        ;;
      *)
        abort
        ;;
    esac
  done
'''
free_new = '''  choose_disk_security || return 1

  clear_logo
  echo
  say "Install Omarchy in the $(to_gb $INSTALL_MAX_B) of free space."
  if [[ $encrypt_installation == true ]]; then
    say --foreground 8 "Disk encryption: enabled (LUKS)"
  else
    say --foreground 8 "Disk encryption: skipped — no boot-time LUKS password"
  fi
  echo
  gum confirm --affirmative "Yes, install" --negative "Back" \\
    "Confirm installing on $disk" || return 1
'''
if s.count(free_old) != 1:
    raise SystemExit("Stage A free-space security block changed upstream")
s = s.replace(free_old, free_new, 1)

full_old = '''confirm_disk_overwrite() {
  local mode="encrypted"
  local affirmative confirm_status

  while true; do
    clear_logo
    echo
    say "Everything will be overwritten. There is no recovery possible."

    if [[ $mode == "encrypted" ]]; then
      say --foreground 8 "Press Ctrl+C for unencrypted install."
      affirmative="Yes, install"
    else
      affirmative="Yes, install without encryption"
    fi

    echo
    gum confirm --affirmative "$affirmative" --negative "No, change it" "Confirm overwriting ${disk}"
    confirm_status=$?

    case $confirm_status in
      0)
        [[ $mode == "encrypted" ]] && encrypt_installation=true || encrypt_installation=false
        return 0
        ;;
      1)
        return 1
        ;;
      130)
        [[ $mode == "encrypted" ]] && mode="unencrypted" || mode="encrypted"
        ;;
      *)
        abort
        ;;
    esac
  done
}'''
full_new = '''confirm_disk_overwrite() {
  choose_disk_security || return 1

  clear_logo
  echo
  say "Everything will be overwritten. There is no recovery possible."
  if [[ $encrypt_installation == true ]]; then
    say --foreground 8 "Disk encryption: enabled (LUKS)"
  else
    say --foreground 8 "Disk encryption: skipped — no boot-time LUKS password"
  fi
  echo
  gum confirm --affirmative "Yes, install" --negative "Back" "Confirm overwriting ${disk}"
}'''
if s.count(full_old) != 1:
    raise SystemExit("Stage A full-disk security block changed upstream")
s = s.replace(full_old, full_new, 1)
p.write_text(s)

continuation = chr(92) + "\n"
replace_once(
    "configs/airootfs/root/.automated_script.sh",
    "    --encrypt-file /root/user_encrypt_installation.txt " + continuation,
    "    --encrypt-file /root/user_encrypt_installation.txt " + continuation
    + "    --autologin-file /root/user_autologin.txt " + continuation,
    "Stage A automated-script autologin arg",
)

replace_once(
    "configs/airootfs/usr/local/bin/omarchy-iso-install",
    '    --encrypt-file)         export OMARCHY_INSTALL_ENCRYPT_FILE="$2"; shift 2 ;;\n',
    '    --encrypt-file)         export OMARCHY_INSTALL_ENCRYPT_FILE="$2"; shift 2 ;;\n'
    '    --autologin-file)       export OMARCHY_INSTALL_AUTOLOGIN_FILE="$2"; shift 2 ;;\n',
    "Stage A iso-install autologin arg",
)

p = iso / "configs/airootfs/usr/share/omarchy-iso/orchestrator/context.py"
s = p.read_text()
if s.count("    encrypt: bool\n") != 1:
    raise SystemExit("Stage A context dataclass changed upstream")
s = s.replace("    encrypt: bool\n", "    encrypt: bool\n    autologin: bool\n", 1)

ctx_line = '            encrypt=_read_text(os.environ.get("OMARCHY_INSTALL_ENCRYPT_FILE")).lower() in ("true", "yes", "1"),\n'
if s.count(ctx_line) != 1:
    raise SystemExit("Stage A context constructor changed upstream")
s = s.replace(
    ctx_line,
    ctx_line
    + '            autologin=_read_text(os.environ.get("OMARCHY_INSTALL_AUTOLOGIN_FILE")).lower() in ("true", "yes", "1"),\n',
    1,
)
p.write_text(s)

p = iso / "configs/airootfs/usr/share/omarchy-iso/orchestrator/phases_impl.py"
s = p.read_text()
login_condition = "    if ctx.encrypt and not ctx.defer_provisioning:\n"
if s.count(login_condition) != 1:
    raise SystemExit("Stage A configure_login condition changed upstream")
s = s.replace(login_condition, "    if ctx.autologin and not ctx.defer_provisioning:\n", 1)
p.write_text(s)

p = iso / "bin/omarchy-iso-test"
s = p.read_text()

normal_timezone = '''  wait_for_screen "Timezone" 180 # tzupdate geo-guess can take a moment
  capture_console "success-installer-08-timezone"
  press ret

  wait_for_screen "look right" 60'''
normal_timezone_new = '''  wait_for_screen "Timezone" 180 # tzupdate geo-guess can take a moment
  capture_console "success-installer-08-timezone"
  press ret

  wait_for_screen "Desktop login" 60
  capture_console "success-installer-09-desktop-login"
  press ret # LUNOR default: Automatic login

  wait_for_screen "look right" 60'''
if s.count(normal_timezone) != 1:
    raise SystemExit("Stage A VM harness direct login choice changed upstream")
s = s.replace(normal_timezone, normal_timezone_new, 1)

provision_timezone = '''  wait_for_screen "Timezone" 180
  capture_console "success-provision-06-timezone"
  press ret

  wait_for_screen "look right" 60'''
provision_timezone_new = '''  wait_for_screen "Timezone" 180
  capture_console "success-provision-06-timezone"
  press ret

  wait_for_screen "Desktop login" 60
  capture_console "success-provision-07-desktop-login"
  press ret # LUNOR default: Automatic login

  wait_for_screen "look right" 60'''
if s.count(provision_timezone) != 1:
    raise SystemExit("Stage A VM harness provision login choice changed upstream")
s = s.replace(provision_timezone, provision_timezone_new, 1)

provision_security = '''    wait_for_screen "recovery possible" 60
    capture_console "success-installer-04-prepare-disk-warning-encrypted"
    if ! $ENCRYPT; then
      press ctrl-c
      # The toggled confirm ("Yes, install without encryption") is a highlighted
      # button OCR cannot read, so don't wait for it. A failed toggle still
      # surfaces: the encrypted install stalls at the LUKS prompt on first boot
      # and SSH never comes up.
      sleep 2
      capture_console "success-installer-05-prepare-disk-warning-unencrypted"
    fi
    press ret'''
provision_security_new = '''    wait_for_screen "Disk security" 60
    capture_console "success-installer-04-prepare-disk-security"
    $ENCRYPT && press down
    press ret

    wait_for_screen "recovery possible" 60
    capture_console "success-installer-05-prepare-disk-warning"
    press ret'''
if s.count(provision_security) != 1:
    raise SystemExit("Stage A VM harness provision disk security changed upstream")
s = s.replace(provision_security, provision_security_new, 1)

mode_gate_old = '''  wait_for_screen "installation mode\\|recovery possible" 60
  if ocr_screen | grep -qi "installation mode"; then
    capture_console "success-installer-11-install-mode"
    press ret # "Full disk install" is preselected
  fi
'''
mode_gate_new = '''  wait_for_screen "installation mode\\|Disk security" 60
  if ocr_screen | grep -qi "installation mode"; then
    capture_console "success-installer-11-install-mode"
    press ret # "Full disk install" is preselected
  fi
'''
if s.count(mode_gate_old) != 1:
    raise SystemExit("Stage A VM harness install-mode gate changed upstream")
s = s.replace(mode_gate_old, mode_gate_new, 1)

normal_security = '''  wait_for_screen "recovery possible" 60
  capture_console "success-installer-12-disk-warning-encrypted"
  if ! $ENCRYPT; then
    press ctrl-c # toggles the confirm to the unencrypted flow
    # The toggled confirm ("Yes, install without encryption") is a highlighted
    # button OCR cannot read, so don't wait for it. A failed toggle still
    # surfaces: the encrypted install stalls at the LUKS prompt on first boot
    # and SSH never comes up.
    sleep 2
    capture_console "success-installer-13-disk-warning-unencrypted"
  fi
  press ret'''
normal_security_new = '''  wait_for_screen "Disk security" 60
  capture_console "success-installer-12-disk-security"
  $ENCRYPT && press down
  press ret

  wait_for_screen "recovery possible" 60
  capture_console "success-installer-13-disk-warning"
  press ret'''
if s.count(normal_security) != 1:
    raise SystemExit("Stage A VM harness direct disk security changed upstream")
s = s.replace(normal_security, normal_security_new, 1)
p.write_text(s)

checks = {
    "configs/airootfs/root/configurator": [
        "omarchy_prompt_login_mode",
        "user_autologin.txt",
        "Disk security",
        "No disk encryption (boot without LUKS password)",
    ],
    "configs/airootfs/usr/local/bin/omarchy-iso-install": [
        "OMARCHY_INSTALL_AUTOLOGIN_FILE",
    ],
    "configs/airootfs/usr/share/omarchy-iso/orchestrator/context.py": [
        "autologin: bool",
        "OMARCHY_INSTALL_AUTOLOGIN_FILE",
    ],
    "configs/airootfs/usr/share/omarchy-iso/orchestrator/phases_impl.py": [
        "ctx.autologin",
    ],
    "bin/omarchy-iso-test": [
        "Desktop login",
        "Disk security",
    ],
}
for rel, needles in checks.items():
    text = (iso / rel).read_text()
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"Stage A validation failed in {rel}: {missing}")
