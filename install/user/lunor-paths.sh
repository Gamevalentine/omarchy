#!/bin/bash

# Migrate early LUNOR/Omarchy-derived user data to the LUNOR namespace.
# Temporary compatibility links keep older scripts functional while the
# remaining internal namespace is migrated in later, isolated steps.

set -euo pipefail

migrate_root() {
  local legacy="$1"
  local target="$2"
  local backup

  mkdir -p "$(dirname "$target")"

  if [[ -L "$legacy" ]]; then
    if [[ "$(readlink -f "$legacy" 2>/dev/null || true)" == "$target" ]]; then
      mkdir -p "$target"
      return 0
    fi
    rm -f "$legacy"
  fi

  if [[ -d "$legacy" && ! -e "$target" ]]; then
    mv "$legacy" "$target"
  elif [[ -d "$legacy" && -d "$target" ]]; then
    # Preserve both trees. Existing LUNOR files win; legacy-only files are copied.
    cp -a -n "$legacy/." "$target/" 2>/dev/null || true
    backup="${legacy}.pre-lunor"
    if [[ ! -e "$backup" ]]; then
      mv "$legacy" "$backup"
    else
      rm -rf "$legacy"
    fi
  fi

  mkdir -p "$target"
  ln -sfn "$target" "$legacy"
}

migrate_root "$HOME/.config/omarchy" "$HOME/.config/lunor"
migrate_root "$HOME/.local/state/omarchy" "$HOME/.local/state/lunor"
