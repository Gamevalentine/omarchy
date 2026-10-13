#!/usr/bin/env bash
# One-time browser preview of real LUNOR OS in a disposable QEMU VM.
set -Eeuo pipefail
cd "$GITHUB_WORKSPACE"
vm_container="lunor-web-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
mkdir -p preview-debug
cleanup() {
  docker rm -f "$vm_container" >/dev/null 2>&1 || true
  for name in cloudflared websockify; do
    [[ ! -f "preview-debug/$name.pid" ]] || kill "$(cat "preview-debug/$name.pid")" >/dev/null 2>&1 || true
  done
}
trap cleanup EXIT

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
      -usb -device usb-tablet -netdev user,id=net0 \
      -device virtio-net-pci,netdev=net0 \
      -pidfile /w/preview-debug/qemu.pid -serial file:/w/preview-debug/serial.log -daemonize
    echo "LUNOR_PREVIEW_VM_RUNNING"
    while kill -0 "$(cat /w/preview-debug/qemu.pid)" 2>/dev/null; do sleep 4; done
    echo "LUNOR VM exited" >&2
    exit 1
  ' >preview-debug/install.log 2>&1 &
docker_pid=$!

deadline=$((SECONDS+1800))
until (echo >/dev/tcp/127.0.0.1/5900) >/dev/null 2>&1; do
  if ! kill -0 "$docker_pid" 2>/dev/null; then
    echo "::error::VM installation failed."
    tail -n 80 preview-debug/install.log || true
    exit 1
  fi
  if (( SECONDS >= deadline )); then
    echo "::error::VM did not start within 30 minutes."
    tail -n 80 preview-debug/install.log || true
    exit 1
  fi
  sleep 5
done

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
echo "Browser proxy is password protected. No secret is logged."
echo "Disposable VM demo login: omarchy / omarchy"
echo "Preview session expires automatically in 35 minutes. Do not save personal data."

curl --max-time 10 -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/ | grep -qx 401
end=$((SECONDS+2100))
while (( SECONDS < end )); do
  if ! kill -0 "$docker_pid" 2>/dev/null; then
    echo "::error::LUNOR VM ended unexpectedly."
    tail -n 80 preview-debug/install.log || true
    exit 1
  fi
  kill -0 "$(cat preview-debug/cloudflared.pid)" 2>/dev/null || {
    echo "::error::Cloudflare tunnel disconnected."
    exit 1
  }
  sleep 15
done
echo "Temporary demo session expired; shutting down VM and tunnel."
