# LUNOR external USB image — isolated feasibility test

Status: **experimental**. Not a downloadable OS image yet.

This GitHub Actions workflow reuses the LUNOR ISO from the successful QA run (`37935766465`) and the upstream QEMU installer harness. It installs the OS to an isolated 40 GiB virtual disk, checks the EFI System Partition for `EFI/BOOT/BOOTX64.EFI`, and tries to boot that installed disk over an emulated USB storage controller with fresh UEFI firmware variables.

The workflow uploads **only small diagnostic reports**, never the installed disk image. The existing harness uses a fixed test user and password and injects a test SSH key; this output is not safe for distribution. Before any end-user `.img` is released, it must be built with first-boot account creation or another properly audited provisioning flow, no test SSH access, and a portable USB-capable initramfs. Successful QEMU testing cannot prove boot compatibility with a specific laptop.

This runner does not connect to the user's Windows disks or Kingston USB. The ISO artifact used by the job expires seven days after generation.