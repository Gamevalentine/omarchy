# LUNOR Web — Cloudflare Pages portal

This is the **real-LUNOR testing portal**, not a JavaScript OS simulation. The stable Cloudflare Pages URL remains available even when there is no test VM. The actual LUNOR desktop is **not** running on Cloudflare Pages and still needs a separate QEMU/KVM host with a secure Cloudflare Tunnel/noVNC connection.

## Deploy to your Cloudflare account (Git integration, without CMD)

1. Sign in to [Cloudflare dashboard](https://dash.cloudflare.com/) > **Workers & Pages** > **Create** > **Pages** > **Connect to Git**.
2. Authorize the GitHub repository **Gamevalentine/omarchy**.
3. Choose production branch: `lunor/cloudflare-pages`.
4. Set **Root directory**: `cloudflare-pages`.
5. Framework: **None**. Build command: `exit 0`; output directory: `public`.
6. Deploy; Cloudflare will assign a fixed `*.pages.dev` URL. You can later attach your own domain.

The `functions/api/status.js` Pages Function requests only **public GitHub Actions run metadata**, cached for a short duration. It does not start or control a VM and intentionally never falsely reports a booted desktop as ready.

## Not implemented (must not be hidden from the user)
- An authenticated real desktop behind a persistent Cloudflare Tunnel hostname.
- A machine hosting LUNOR as a persistent or reusable QEMU image.
- An authorized, bounded start/stop remote session controller.
- Verified end-to-end mouse, keyboard, Hyprland session and application testing.

Cloudflare Pages/Workers do **not** directly run the full LUNOR x86_64 desktop virtual machine. A real host is required. Do not point this portal at an expired `trycloudflare.com` URL or pretend the portal is a running OS. Avoid publishing demo credentials or Cloudflare API tokens. Do not pay for compute or modify the Windows laptop without user permission.

## Test checklist
- Cloudflare Pages deployment returns HTTP 200 for `/`.
- `/api/status` returns JSON with `backendConnected:false` and `desktopVerified:false`.
- The GitHub Actions button resolves to the actual workflow.
- Page labels any running workflow as **preparing**, not a healthy desktop.
- No embedded fake desktop and no hardcoded expired tunnel URLs.
