: "${LUNOR_INSTALL:=${OMARCHY_INSTALL:-${LUNOR_PATH:-${OMARCHY_PATH:-/usr/share/lunor}}/install}}"
OMARCHY_INSTALL=$LUNOR_INSTALL
export LUNOR_INSTALL OMARCHY_INSTALL

run_logged "$LUNOR_INSTALL/user/lunor-paths.sh"
run_logged "$LUNOR_INSTALL/user/theme.sh"
run_logged "$LUNOR_INSTALL/user/chromium.sh"
run_logged "$LUNOR_INSTALL/user/git.sh"
run_logged "$LUNOR_INSTALL/user/xcompose.sh"
run_logged "$LUNOR_INSTALL/user/mise-work.sh"

run_logged "$LUNOR_INSTALL/user/hardware/asus/fix-audio-mixer.sh"
run_logged "$LUNOR_INSTALL/user/hardware/asus/fix-mic.sh"
run_logged "$LUNOR_INSTALL/user/hardware/framework/fix-f13-amd-audio-input.sh"
run_logged "$LUNOR_INSTALL/user/hardware/dell/xps13-text-scaling.sh"
run_logged "$LUNOR_INSTALL/user/hardware/fix-nouveau-cursor.sh"
run_logged "$LUNOR_INSTALL/user/hardware/vm-no-animations.sh"

run_logged "$LUNOR_INSTALL/user/default-keyring.sh"
run_logged "$LUNOR_INSTALL/user/mise.sh"
