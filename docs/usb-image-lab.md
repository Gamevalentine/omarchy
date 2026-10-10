# LUNOR USB delivery — audit and acceptance plan

Status: **experimental**. No end-user disk image is ready.

## Confirmed
- The LUNOR ISO built and passed a complete VM test in [Run 37935766465](https://github.com/Gamevalentine/omarchy/actions/runs/37935766465).
- [USB lab Run #2](https://github.com/Gamevalentine/omarchy/actions/runs/38040758723) installed LUNOR to a 40 GiB virtual disk. Its log confirmed the UEFI removable boot file and successful boot using fresh UEFI settings and an emulated USB mass-storage controller.
- Run #2 failed *after* these checks, while packaging a report. The USB lab now excludes the inaccessible serial log from the upload allowlist.
- [Fast safety CI](https://github.com/Gamevalentine/omarchy/actions/workflows/lunor-usb-static-check.yml) checks guardrails without downloading the ISO or booting a VM.

## Release blockers
1. The virtual disk produced by the test harness contains a demo login and test SSH authorization. **Never publish it as a USB image.**
2. A separate, uninitialized first-boot image must be built using the existing deferred owner-setup facility. It must be examined to ensure no test login or test authorization remains.
3. The generic boot path must work on USB hardware unlike the build VM. The current mkinitcpio configuration contains the `autodetect` hook; evaluate a portable initramfs before physical testing.
4. Confirm UEFI fallback, partition map, disk capacity, fresh hardware boot, and repeatable checksums.
5. The ISO is a seven-day retention GitHub Actions artifact. Check availability before a future run.

## Stages
A. **Safety and source freeze:** isolate changes in `lunor/usb-image-lab`, pin the upstream ISO tooling revision, guard artifact contents and timeouts, pass fast CI.
B. **Test-tool repair:** reuse successful installation/USB-emulation evidence instead of running repeated full installs to chase a report packaging error.
C. **User-ready image:** design a factory-first-boot disk image, block demo credentials, test a private copy on emulated USB, and provide a checksum only if every gate passes.
D. **Physical USB:** after C succeeds, select and erase only the Kingston 64 GB installer stick; boot with the laptop's one-time HP F9 menu. Never modify Windows/BitLocker partitions or the external SSD.

## Excluded paths
- Do not try VirtualBox USB passthrough again; a host freeze occurred.
- Do not install LUNOR onto the same USB currently running its installer.
- Do not silently merge into `lunor/1.0-clean-branding` or produce a public image from the present QA disk.

This document is a release gate. Simulated USB boot does not by itself prove the laptop will boot.
