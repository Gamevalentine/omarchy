#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: lunor-quickshell-fallback.py <omarchy-iso-dir>")

p = Path(sys.argv[1]) / "builder/build-iso.sh"
s = p.read_text()

filter_old = """if [[ -n ${LOCAL_OMARCHY_BUILD:-} ]]; then
  mapfile -t all_packages < <(
    printf '%s\\n' "${all_packages[@]}" |
      grep -Fxv \\
        -e "$OMARCHY_RUNTIME_PACKAGE" \\
        -e "$OMARCHY_SETTINGS_PACKAGE" \\
        -e "$OMARCHY_NVIM_PACKAGE" || true
  )
fi

mkdir -p /tmp/offlinedb
"""

filter_new = """if [[ -n ${LOCAL_OMARCHY_BUILD:-} ]]; then
  mapfile -t all_packages < <(
    printf '%s\\n' "${all_packages[@]}" |
      grep -Fxv \\
        -e "$OMARCHY_RUNTIME_PACKAGE" \\
        -e "$OMARCHY_SETTINGS_PACKAGE" \\
        -e "$OMARCHY_NVIM_PACKAGE" \\
        -e quickshell || true
  )
fi

# LUNOR: pkgs.omarchy.org currently advertises quickshell-0.3.2-1 but the
# package object returns 404. The current LUNOR desktop is already validated
# with Arch Extra's quickshell, so fetch that one separately.
arch_only_conf=/tmp/lunor-pacman-arch-only.conf
awk '
  /^\\[omarchy\\]$/ { skip=1; next }
  skip && /^\\[/ { skip=0 }
  !skip { print }
' "/configs/pacman-online-${OMARCHY_MIRROR}.conf" >"$arch_only_conf"

rm -f "$offline_mirror_dir"/quickshell-*.pkg.tar.*
rm -rf /tmp/lunor-quickshell-db
mkdir -p /tmp/lunor-quickshell-db
pacman --config "$arch_only_conf" --noconfirm -Syw quickshell \\
  --cachedir "$offline_mirror_dir/" --dbpath /tmp/lunor-quickshell-db --needed

mkdir -p /tmp/offlinedb
"""

if s.count(filter_old) != 1:
    raise SystemExit("Upstream local package filter changed; review LUNOR quickshell fallback")
s = s.replace(filter_old, filter_new, 1)

keep_old = """fi

printf '%s\\n' "${required_package_files[@]}" |
  bash /builder/prune-offline-mirror.sh "$offline_mirror_dir"
"""

keep_new = """fi

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

printf '%s\\n' "${required_package_files[@]}" |
  bash /builder/prune-offline-mirror.sh "$offline_mirror_dir"
"""

if s.count(keep_old) != 1:
    raise SystemExit("Upstream package keep-set changed; review LUNOR quickshell fallback")
s = s.replace(keep_old, keep_new, 1)

p.write_text(s)
print("Applied LUNOR Arch Extra quickshell fallback")
