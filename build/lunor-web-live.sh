#!/usr/bin/env bash
# One-time browser preview of real LUNOR OS in a disposable QEMU VM.
set -Eeuo pipefail
cd "$GITHUB_WORKSPACE"
vm_container="lunor-web-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
mkdir -p preview-debug
# This phase returns immediately after desktop and HTTPS are READY.
# The next GitHub Actions step holds the session open, and final cleanup is always separate.

sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nginx novnc websockify curl
sudo install -m 0640 -o root -g www-data "lunor-source/build/lunor-web-htpasswd" /etc/nginx/lunor-web-htpasswd
sudo tee /etc/nginx/sites-available/lunor-web >/dev/null <<'NGINX'
server {
  listen 127.0.0.1:8080;
  server_name _;
  auth_basic "LUNOR private browser preview";
  auth_basic_user_file /etc/nginx/lunor-web-htpasswd;
  location / {
    proxy_pass http://127.0.0.1:6080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 3600;
    proxy_send_timeout 3600;
    proxy_buffering off;
  }
}
NGINX
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/lunor-web /etc/nginx/sites-enabled/lunor-web
sudo nginx -t
sudo systemctl restart nginx
websockify --web /usr/share/novnc 127.0.0.1:6080 127.0.0.1:5900 > preview-debug/websockify.log 2>&1 &
echo "$!" > preview-debug/websockify.pid
# Authentication must reject all clients before exposing tunnel.
curl --max-time 10 -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/vnc.html | grep -qx 401

sudo chmod 0666 /dev/kvm
docker run --name "$vm_container" --rm --device /dev/kvm -p 127.0.0.1:5900:5900 \
  -v "$PWD:/w" -w /w/lunor-iso archlinux:latest bash -euo pipefail -c '
    pacman -Syu --noconfirm --needed \
      qemu-system-x86 qemu-hw-display-virtio-gpu qemu-hw-display-virtio-vga \
      qemu-img edk2-ovmf socat imagemagick tesseract tesseract-data-eng \
      mtools dosfstools jq openssh openssl python curl ripgrep lua >/dev/null
    printf "#!/bin/sh\nexit 0\n" >/usr/local/bin/omarchy-pkg-add
    chmod 0755 /usr/local/bin/omarchy-pkg-add
    export OMARCHY_PATH=/w/lunor-source
    timeout --signal=TERM --kill-after=20s 1600s \
      ./bin/omarchy-iso-test release/*.iso --install-only --no-preview --memory 8192 --timeout 1200
    mapfile -t disks < <(find test-runs -name base.qcow2 -type f)
    (( ${#disks[@]} == 1 )) || { echo "Expected one installed demo disk"; exit 1; }
    base="${disks[0]}"
    qemu-img check -f qcow2 "$base"
    cp /usr/share/edk2/x64/OVMF_VARS.4m.fd /w/preview-debug/fresh-vars.fd
    qemu-system-x86_64 -cpu host -enable-kvm -machine q35,accel=kvm -smp 2 -m 8192 \
      -drive if=pflash,format=raw,readonly=on,file=/usr/share/edk2/x64/OVMF_CODE.4m.fd \
      -drive if=pflash,format=raw,file=/w/preview-debug/fresh-vars.fd \
      -drive "file=$base,format=qcow2,if=none,id=disk0" \
      -device qemu-xhci,id=xhci -device usb-storage,bus=xhci.0,drive=disk0,bootindex=1 \
      -device virtio-vga -display none -vnc 0.0.0.0:0 \
      -usb -device usb-tablet -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2233-:22 \
      -device virtio-net-pci,netdev=net0 \
      -qmp unix:/w/preview-debug/desktop-qmp.sock,server,nowait \
      -pidfile /w/preview-debug/qemu.pid -serial file:/w/preview-debug/serial.log -daemonize
    echo "LUNOR_PREVIEW_VM_RUNNING"
    guest_key="$(dirname "$base")/id_ed25519"
    guest() {
      timeout 12s ssh -i "$guest_key" -p 2233 -o BatchMode=yes \
        -o IdentitiesOnly=yes -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 \
        -o LogLevel=ERROR omarchy@127.0.0.1 "$1" </dev/null
    }
    echo "Waiting for installed guest SSH, not just VNC port..."
    guest_ssh_ready=false
    for i in $(seq 1 45); do
      if guest "true" >/dev/null 2>&1; then guest_ssh_ready=true; break; fi
      kill -0 "$(cat /w/preview-debug/qemu.pid)" 2>/dev/null || break
      sleep 4
    done
    if ! $guest_ssh_ready; then
      echo "FAIL: installed guest SSH never became ready; no preview link will be published." >&2
      exit 1
    fi
    desktop_ready() {
      guest "test -d /run/user/1000/hypr && find /run/user/1000/hypr -mindepth 1 -maxdepth 1 -print -quit | grep -q ." >/dev/null 2>&1
    }
    qmp_key() {
      key="$1"
      cat <<QMP | socat -t 2 - "UNIX-CONNECT:/w/preview-debug/desktop-qmp.sock" >/dev/null 2>&1
{"execute":"qmp_capabilities"}
{"execute":"send-key","arguments":{"keys":[{"type":"qcode","data":"$key"}]}}
QMP
    }
    echo "Waiting for actual Hyprland desktop. Automating the demo SDDM login if needed..."
    hypr_ready=false
    for i in $(seq 1 24); do
      if desktop_ready; then hypr_ready=true; break; fi
      # The standard unencrypted ISO harness otherwise needs the demo password
      # entered at SDDM; users should not have to do this during timed QA.
      if (( i >= 4 && i % 3 == 1 )); then
        for key in o m a r c h y ret; do qmp_key "$key" || true; sleep 0.15; done
      fi
      kill -0 "$(cat /w/preview-debug/qemu.pid)" 2>/dev/null || break
      sleep 10
    done
    if ! $hypr_ready; then
      echo "FAIL: installed guest did not reach Hyprland desktop. Do not show a premature 60-minute web link." >&2
      exit 1
    fi
    touch /w/preview-debug/desktop-ready
    echo "LUNOR_DESKTOP_READY"
    while kill -0 "$(cat /w/preview-debug/qemu.pid)" 2>/dev/null; do sleep 4; done
    echo "LUNOR VM exited" >&2
    exit 1
  ' >preview-debug/install.log 2>&1 &
docker_pid=$!
echo "$docker_pid" >preview-debug/docker.pid

deadline=$((SECONDS+1800))
# A listening VNC socket alone is NOT desktop readiness.
# Only publish the link after the installed guest confirms an active Hyprland session.
until [[ -f preview-debug/desktop-ready ]]; do
  if ! kill -0 "$docker_pid" 2>/dev/null; then
    echo "::error::VM installation failed."
    tail -n 80 preview-debug/install.log || true
    exit 1
  fi
  if (( SECONDS >= deadline )); then
    echo "::error::LUNOR desktop did not become ready within 30 minutes."
    tail -n 80 preview-debug/install.log || true
    exit 1
  fi
  sleep 5
done

# Guest says Hyprland is ready; also require the current VNC display socket.
(echo >/dev/tcp/127.0.0.1/5900) >/dev/null 2>&1 || {
  echo "::error::Desktop ready but VNC is unreachable."; exit 1;
}
echo "::notice title=LUNOR Desktop Ready::Hyprland is running; preparing the browser session."
curl --retry 3 --retry-delay 2 -fsSL \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o preview-debug/cloudflared
chmod +x preview-debug/cloudflared
preview-debug/cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8080 \
  >preview-debug/cloudflared.log 2>&1 &
echo "$!" > preview-debug/cloudflared.pid
url=""
for _ in $(seq 1 30); do
  url=$(grep -Eo 'https://[a-z0-9-]+[.]trycloudflare[.]com' preview-debug/cloudflared.log | head -n 1 || true)
  [[ -z "$url" ]] || break
  kill -0 "$(cat preview-debug/cloudflared.pid)" 2>/dev/null || {
    echo "::error::Cloudflare tunnel stopped."
    tail -n 30 preview-debug/cloudflared.log
    exit 1
  }
  sleep 2
done
if [[ -z "$url" ]]; then
  echo "::error::Temporary HTTPS tunnel did not start."
  tail -n 30 preview-debug/cloudflared.log || true
  exit 1
fi
echo "::notice title=LUNOR Browser Preview::${url}/vnc.html"
echo "LUNOR HTTPS PREVIEW: $url/vnc.html?autoconnect=1&resize=scale"
# Surface the link on GitHub Actions Summary so testers do not need to search logs.
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  {
    printf '## LUNOR OS — Trải nghiệm trực tiếp trên web\n\n'
    printf 'Mở trong khi job đang chạy: [**Vào LUNOR OS**](%s/vnc.html?autoconnect=1)\n\n' "$url"
    printf 'Phiên dùng thử 60 phút kể từ lúc link được tạo. Link tạm tự hết hạn khi job kết thúc.\n'
    printf 'Chỉ dùng dữ liệu thử nghiệm; không lưu thông tin cá nhân.\n'
  } >> "$GITHUB_STEP_SUMMARY"
fi
echo "Browser proxy is password protected. No secret is logged."
echo "Disposable VM demo login: omarchy / omarchy"
echo "Preview session expires automatically in 60 minutes. Do not save personal data."

curl --max-time 10 -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/ | grep -qx 401
# This step must now COMPLETE while the VM/tunnel remain online.
# GitHub can publish the link in the run summary before the hold-open step ends.
date +%s > preview-debug/ready-at-epoch.txt
printf '%s\n' "$url" > preview-debug/preview-url.txt
echo "::notice title=LUNOR Ready Now::Open the link in the run summary while the next job step runs."
echo "LUNOR_WEB_READY_STEP_COMPLETE: the 60-minute hold happens in the next workflow step."
