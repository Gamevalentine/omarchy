mkdir -p ~/.config/lunor

cat >~/.config/lunor/agent.conf <<EOF
helper=$HOME/.local/share/omarchy/bin/omarchy-agent
EOF

cat >"$HOME/.local/bin/omarchy-shim" <<EOF
exec "$OMARCHY_PATH/bin/omarchy-agent" "$@"
EOF
