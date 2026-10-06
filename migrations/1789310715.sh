echo "Install cf (Cloudflare CLI) via mise wrapper"

if [[ ! -f $HOME/.local/state/lunor/preinstalls-removed ]]; then
  omarchy-mise-install npm:cf cf
fi
