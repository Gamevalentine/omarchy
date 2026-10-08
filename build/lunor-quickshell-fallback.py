#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: lunor-quickshell-fallback.py <omarchy-iso-dir>")

iso = Path(sys.argv[1])
p = iso / "builder/build-iso.sh"
s = p.read_text()

filter_anchor = r'''if [[ -n ${LOCAL_OMARCHY_BUILD:-} ]]; then
  mapfile -t all_packages < <(
    printf '%s\n' "${all_packages[@]}" |
      grep -Fxv \
        -e "$OMARCHY_RUNTIME_PACKAGE" \
        -e "$OMARCHY_SETTINGS_PACKAGE" \
        -e "$OMARCHY_NVIM_PACKAGE" || true
  )
fi

mkdir -p /tmp/offlinedb
'''

filter_replacement = r'''if [[ -n ${LOCAL_OMARCHY_BUILD:-} ]]; then
  mapfile -t all_packages < <(
    printf '%s\n' "${all_packages[@]}" |
      grep -Fxv \
        -e "$OMARCHY_RUNTIME_PACKAGE" \
        -e "$OMARCHY_SETTINGS_PACKAGE" \
        -e "$OMARCHY_NVIM_PACKAGE" || true
  )
fi

# LUNOR build resilience: the Omarchy repository database can briefly point at
# a quickshell object that has not reached (or has already left) the CDN. Pacman
# then reports the 404 response as "Maximum file size exceeded". Keep the normal
# Omarchy quickshell whenever its object exists; otherwise use Arch Extra's
# quickshell, which is already validated by the current LUNOR desktop.
LUNOR_QUICKSHELL_FALLBACK=""
quickshell_probe_db=/tmp/lunor-quickshell-probe
rm -rf "$quickshell_probe_db"
mkdir -p "$quickshell_probe_db"
pacman --config "/configs/pacman-online-${OMARCHY_MIRROR}.conf" --noconfirm \
  -Sy --dbpath "$quickshell_probe_db" >/dev/null
quickshell_url="$(pacman --config "/configs/pacman-online-${OMARCHY_MIRROR}.conf" \
  --dbpath "$quickshell_probe_db" --noconfirm -Sdd --print --print-format '%l' quickshell | head -1 || true)"

if [[ -z $quickshell_url ]] || ! curl --retry 2 --retry-all-errors -fsSI "$quickshell_url" >/dev/null; then
  echo "Omarchy quickshell object is unavailable; using Arch Extra quickshell for this LUNOR build." >&2
  LUNOR_QUICKSHELL_FALLBACK=1

  mapfile -t all_packages < <(
    printf '%s\n' "${all_packages[@]}" | grep -Fxv quickshell || true
  )

  arch_only_conf=/tmp/lunor-pacman-arch-only.conf
  awk '
    /^\[omarchy\]$/ { skip=1; next }
    skip && /^\[/ { skip=0 }
    !skip { print }
  ' "/configs/pacman-online-${OMARCHY_MIRROR}.conf" >"$arch_only_conf"

  rm -f "$offline_mirror_dir"/quickshell-*.pkg.tar.*
  rm -rf /tmp/lunor-quickshell-arch-db
  mkdir -p /tmp/lunor-quickshell-arch-db
  pacman --config "$arch_only_conf" --noconfirm -Syw quickshell \
    --cachedir "$offline_mirror_dir/" --dbpath /tmp/lunor-quickshell-arch-db --needed
fi

mkdir -p /tmp/offlinedb
'''

if s.count(filter_anchor) != 1:
    raise SystemExit("Upstream local-package filter changed; review LUNOR quickshell fallback patch")
s = s.replace(filter_anchor, filter_replacement, 1)

keep_anchor = r'''if [[ -n ${LOCAL_OMARCHY_BUILD:-} ]]; then
  for local_package_name in \
    "$OMARCHY_RUNTIME_PACKAGE" "$OMARCHY_SETTINGS_PACKAGE" "$OMARCHY_NVIM_PACKAGE"; do
    local_package_file=""
    for candidate in "$offline_mirror_dir/$local_package_name-"*.pkg.tar.*; do
      [[ -f $candidate && $candidate != *.sig ]] || continue
      read -r candidate_name _ < <(pacman -Qp "$candidate" 2>/dev/null) || continue
      [[ $candidate_name == "$local_package_name" ]] || continue
      if [[ -n $local_package_file ]]; then
        echo "ERROR: multiple local builds found for $local_package_name" >&2
        exit 1
      fi
      local_package_file="${candidate##*/}"
    done
    if [[ -z $local_package_file ]]; then
      echo "ERROR: local build not found for $local_package_name" >&2
      exit 1
    fi
    required_package_files+=("$local_package_file")
  done
fi

printf '%s\n' "${required_package_files[@]}" |
'''

keep_replacement = r'''if [[ -n ${LOCAL_OMARCHY_BUILD:-} ]]; then
  for local_package_name in \
    "$OMARCHY_RUNTIME_PACKAGE" "$OMARCHY_SETTINGS_PACKAGE" "$OMARCHY_NVIM_PACKAGE"; do
    local_package_file=""
    for candidate in "$offline_mirror_dir/$local_package_name-"*.pkg.tar.*; do
      [[ -f $candidate && $candidate != *.sig ]] || continue
      read -r candidate_name _ < <(pacman -Qp "$candidate" 2>/dev/null) || continue
      [[ $candidate_name == "$local_package_name" ]] || continue
      if [[ -n $local_package_file ]]; then
        echo "ERROR: multiple local builds found for $local_package_name" >&2
        exit 1
      fi
      local_package_file="${candidate##*/}"
    done
    if [[ -z $local_package_file ]]; then
      echo "ERROR: local build not found for $local_package_name" >&2
      exit 1
    fi
    required_package_files+=("$local_package_file")
  done
fi

if [[ -n ${LUNOR_QUICKSHELL_FALLBACK:-} ]]; then
  fallback_quickshell_file=""
  for candidate in "$offline_mirror_dir"/quickshell-*.pkg.tar.*; do
    [[ -f $candidate && $candidate != *.sig ]] || continue
    read -r candidate_name _ < <(pacman -Qp "$candidate" 2>/dev/null) || continue
    [[ $candidate_name == quickshell ]] || continue
    if [[ -n $fallback_quickshell_file ]]; then
      echo "ERROR: multiple quickshell fallback packages found" >&2
      exit 1
    fi
    fallback_quickshell_file="${candidate##*/}"
  done
  if [[ -z $fallback_quickshell_file ]]; then
    echo "ERROR: Arch Extra quickshell fallback was not downloaded" >&2
    exit 1
  fi
  required_package_files+=("$fallback_quickshell_file")
fi

printf '%s\n' "${required_package_files[@]}" |
'''

if s.count(keep_anchor