#!/usr/bin/env bash
# Hold an ALREADY READY desktop session open after the startup step completed.
# Crucial: GitHub Actions run-summary links become visible before this step finishes.
set -Eeuo pipefail
cd "$GITHUB_WORKSPACE"
vm_container="lunor-web-$GITHUB_RUN_ID-$GITHUB_RUN_ATTEMPT"
test -s preview-debug/ready-at-epoch.txt || {
  echo "::error::Desktop readiness marker missing. Refuse to count down preview time."; exit 1;
}
test -s preview-debug/preview-url.txt || {
  echo "::error::Preview URL missing. Refuse to hold a broken session."; exit 1;
}
start=$(cat preview-debug/ready-at-epoch.txt)
[[ "$start" =~ ^[0-9]+$ ]] || { echo "::error::Invalid ready timestamp"; exit 1; }
end=$((start+3600))
echo "::notice title=LUNOR Desktop Live::Open the link in the workflow Summary now; this step remains active for up to 60 minutes."
echo "READY_FOR_INTERACTIVE_TESTING; timer begins only after Hyprland readiness and HTTPS link were verified."
while (( $(date +%s) < end )); do
  running=$(docker inspect -f "{{.State.Running}}" "$vm_container" 2>/dev/null || true)
  [[ "$running" == "true" ]] || { echo "::error::LUNOR VM exited before session timeout"; exit 1; }
  for service in websockify cloudflared; do
    file="preview-debug/$service.pid"
    [[ -s "$file" ]] && kill -0 "$(cat "$file")" 2>/dev/null || {
      echo "::error::LUNOR browser bridge $service stopped early"; exit 1;
    }
  done
  sleep 10
done
echo "60 minutes of ready-desktop preview elapsed; finishing test session."
