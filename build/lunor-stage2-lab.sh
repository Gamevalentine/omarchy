#!/usr/bin/env bash
# Stage 2, isolated QA only: install LUNOR once, then reboot twice using one QCOW2 base.
# Never publish the demo base image. This script runs inside GitHub Actions Docker.
set -Eeuo pipefail
: "${LUNOR_STAGE2_ISOLATED:?Run only on isolated CI; never against physical disks}"
[[ "$LUNOR_STAGE2_ISOLATED" == "YES" ]] || exit 1
[[ "$PWD" == "/w/lunor-iso" ]] || { echo "Requires /w/lunor-iso workdir"; exit 1; }
[[ -e /dev/kvm ]] || { echo "KVM unavailable"; exit 1; }
[[ -d /w/lunor-source ]] || { echo "Source checkout missing"; exit 1; }
[[ -d release ]] || exit 1
[[ "$(find release -maxdepth 1 -type f -name '*.iso' | wc -l)" -eq 1 ]] || exit 1
[[ "$(find release -maxdepth 1 -type f -name '*.sha256' | wc -l)" -eq 1 ]] || exit 1
sha256sum -c release/*.sha256

export OMARCHY_PATH=/w/lunor-source
mkdir -p /w/stage2-report
iso=$(find release -maxdepth 1 -type f -name '*.iso' -print -quit)
printf 'source_commit=%s\n' "$(< /w/stage2-report/source-commit.txt)" > /w/stage2-report/summary.txt
printf 'upstream_iso_harness_commit=%s\n' "$(< /w/stage2-report/upstream-commit.txt)" >> /w/stage2-report/summary.txt
printf 'iso_sha256=%s\n' "$(sha256sum "$iso" | awk '{print $1}')" >> /w/stage2-report/summary.txt
printf 'storage=ephemeral GitHub Actions runner\nrelease_image=false\n' >> /w/stage2-report/summary.txt

# This harness installs an intentionally insecure QA account and test SSH key.
# The QCOW2 and screenshots exist on the ephemeral runner ONLY.
# An end-user/reusable public base needs a separately audited factory-first-boot process.
echo '== Stage 2 installation: one time, no subsequent install!'
timeout --signal=TERM --kill-after=30s 1450s \
  ./bin/omarchy-iso-test "$iso" --install-only --no-preview --memory 8192 --timeout 1150
mapfile -t bases < <(find test-runs -type f -name base.qcow2)
(( ${#bases[@]} == 1 )) || { echo "Expected exactly one installed QCOW2" >&2; exit 1; }
base="${bases[0]}"
qemu-img check -f qcow2 "$base"
qemu-img info -f qcow2 --output=json "$base" | jq -e '."virtual-size" == 42949672960 and .format == "qcow2"' >/dev/null
initial_sha=$(sha256sum "$base" | awk '{print $1}')
printf 'base_sha256_before_reboots=%s\n' "$initial_sha" >> /w/stage2-report/summary.txt
printf 'virtual_disk_bytes=42949672960\n' >> /w/stage2-report/summary.txt
echo '== Preinstalled VM image exists. Two fresh boots reuse it, not reinstall.'

for boot_number in 1 2; do
  echo "== Installed LUNOR repeat boot ${boot_number}/2 (read-only base, writable transient overlay)."
  timeout --signal=TERM --kill-after=30s 500s \
    ./bin/omarchy-iso-test "$iso" --reuse-base --no-preview --memory 8192 --timeout 420
  desktop_count=$(find test-runs -type f -name 'success-session-03-desktop.png' | wc -l)
  (( desktop_count >= boot_number )) || {
    echo "No Hyprland desktop acceptance screenshot for boot ${boot_number}" >&2
    exit 1
  }
  actual_sha=$(sha256sum "$base" | awk '{print $1}')
  [[ "$actual_sha" == "$initial_sha" ]] || {
    echo "Installed base mutated after boot ${boot_number}" >&2
    exit 1
  }
  qemu-img check -f qcow2 "$base"
  printf 'boot_%s=PASS (reused installed base; Hyprland acceptance completed)\n' "$boot_number" >> /w/stage2-report/summary.txt
done

printf 'base_sha256_after_reboots=%s\n' "$(sha256sum "$base" | awk '{print $1}')" >> /w/stage2-report/summary.txt
printf 'qa_result=PASS\n' >> /w/stage2-report/summary.txt
printf 'public_distribution=BLOCKED: demo credentials, test SSH key, no persistent storage\n' >> /w/stage2-report/summary.txt
echo '== STAGE2 REUSE QA PASSED: no reinstall on boot 1 or 2'
cat /w/stage2-report/summary.txt
