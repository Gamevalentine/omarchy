#!/usr/bin/env bash
# Lab-only: installed VM disk contains test credentials, NEVER publish it.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
iso_dir="${LUNOR_ISO_DIR:-$root/../lunor-iso}"
out="$root/usb-image-lab-report"
mkdir -p "$out"
mapfile -t disks < <(find "$iso_dir/test-runs" -name base.qcow2 -type f)
(( ${#disks[@]} == 1 )) || { echo 'Expected precisely one installed base image' >&2; exit 1; }
base="${disks[0]}"
base_dir="$(dirname "$base")"
[[ -s "$base_dir/id_ed25519" ]] || { echo 'Test SSH key missing' >&2; exit 1; }
qemu-img check -f qcow2 "$base" | tee "$out/qcow2-check.txt"
qemu-img info --output=json "$base" | jq '{format, virtual_size: .["virtual-size"], actual_size: .["actual-size"]}' | tee "$out/disk-info.json"
size=$(qemu-img info --output=json "$base" | jq -r '."virtual-size"')
(( size <= 60000000000 )) || { echo 'Disk image is too big for USB 64 GB' >&2; exit 1; }

# Probe partition table and EFI fallback without touching host block devices.
raw="$out/disk-probe.raw"
vm_pid=''
cleanup() { rm -f "$raw"; [[ -z "$vm_pid" ]] || kill "$vm_pid" 2>/dev/null || true; }
trap cleanup EXIT
qemu-img convert -f qcow2 -O raw -S 4k "$base" "$raw"
sfdisk --json "$raw" > "$out/partitions.json"
ss=$(jq -r '.partitiontable.sectorsize // 512' "$out/partitions.json")
esp_start=$(jq -r '[.partitiontable.partitions[] | select((.type | ascii_downcase) == "c12a7328-f81f-11d2-ba4b-00a0c93ec93b") | .start][0] // empty' "$out/partitions.json")
[[ "$esp_start" =~ ^[0-9]+$ ]] || { echo 'No GPT EFI System Partition' >&2; exit 1; }
offset=$((ss * esp_start))
if mdir -i "${raw}@@${offset}" ::/EFI/BOOT/BOOTX64.EFI > "$out/efi-fallback.txt" 2>&1; then
  echo 'PASS: EFI/BOOT/BOOTX64.EFI exists.' | tee "$out/efi-result.txt"
else
  echo 'FAIL: UEFI removable-media fallback missing; not safe to flash.' | tee "$out/efi-result.txt"
  exit 1
fi
rm -f "$raw"

# Test with fresh UEFI NVRAM and emulated USB mass-storage controller.
fw=/usr/share/edk2/x64/OVMF_CODE.4m.fd
vars=/usr/share/edk2/x64/OVMF_VARS.4m.fd
cp "$vars" "$out/fresh-nvram.fd"
qemu-system-x86_64 \
  -cpu host -enable-kvm -machine q35,accel=kvm -smp 2 -m 4096 \
  -drive "if=pflash,format=raw,readonly=on,file=$fw" \
  -drive "if=pflash,format=raw,file=$out/fresh-nvram.fd" \
  -drive "file=$base,format=qcow2,if=none,id=disk0" \
  -device qemu-xhci,id=xhci \
  -device usb-storage,bus=xhci.0,drive=disk0,bootindex=1 \
  -device virtio-vga -display none -vnc 127.0.0.1:8 \
  -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2233-:22 \
  -device virtio-net-pci,netdev=net0 \
  -serial "file:$out/boot-serial.log" \
  -pidfile "$out/usb-qemu.pid" -daemonize
vm_pid="$(cat "$out/usb-qemu.pid")"
ready=false
for _ in $(seq 1 48); do
  if timeout 8 ssh -i "$base_dir/id_ed25519" -p 2233 -o BatchMode=yes -o IdentitiesOnly=yes \
    -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ConnectTimeout=4 -o LogLevel=ERROR \
    omarchy@127.0.0.1 'findmnt -n -o SOURCE /; head -n 4 /etc/os-release' \
    > "$out/usb-boot-ssh.txt" 2>/dev/null; then
    ready=true
    break
  fi
  kill -0 "$vm_pid" 2>/dev/null || { echo 'QEMU stopped before OS came up' >&2; break; }
  sleep 5
done
if $ready; then
  echo 'PASS: clean UEFI firmware booted installed OS via emulated USB.' | tee "$out/usb-boot-result.txt"
else
  echo 'FAIL: installed system did not boot from emulated USB.' | tee "$out/usb-boot-result.txt"
  exit 1
fi
echo 'DO NOT DISTRIBUTE: demo username/password and test SSH key remain in VM image.' > "$out/distribution-blocked.txt"
