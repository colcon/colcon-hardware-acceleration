colcon-hardware-acceleration
=========

An extension for [colcon-core](https://github.com/colcon/colcon-core) to include Hardware Acceleration capabilities.


A quick peek into some of the most relevant `verbs` and capabilities:

| verb | quick peek | description |
|------|-------------|------------|
| `select` | [![asciicast](https://asciinema.org/a/434781.svg)](https://asciinema.org/a/434781) | The `select` verb allows to easily select and configure a specific target firmware for hardware acceleration, and default to it while producing binaries and accelerators.  |
| `list` | [![asciicast](https://asciinema.org/a/434781.svg)](https://asciinema.org/a/434781) | The `list` verb  allows to inspect the acceleration firmware available in the colcon workspace, marking with a `*` the currently selected option.  |
| `linux` | [![asciicast](https://asciinema.org/a/scOognokU4wt0PW3E1N4F0jCe.svg)](https://asciinema.org/a/scOognokU4wt0PW3E1N4F0jCe) | The `linux` verb helps configure the Linux kernel in the raw SD card image produced by the firmware. E.g. `colcon acceleration linux vanilla` will produce a Linux vanilla kernel, whereas `colcon acceleration linux preempt_rt` will instead use a pre-built kernel and kernel modules for improved determinism (fully preemptible kernel). |
| `hypervisor`   |  [![asciicast](https://asciinema.org/a/443406.svg)](https://asciinema.org/a/443406) | The `hypervisor` verb helps configure the [Xen](https://xenproject.org/) hypervisor in the raw SD card image produced by the firmware. E.g. `colcon acceleration hypervisor --dom0 vanilla --domU vanilla --dom0less preempt_rt` will produce a raw image leveraging Xen with 3 VMs. The first, `dom0`, uses a vanilla  kernel. The second, `domU`, uses a vanilla kernel. The third is a   `dom0less` VM and uses a fully preemtible kernel   (*preemt_rt*). Unless otherwise specified, all VMs use  the default ROS 2 configuration, PetaLinux-based  rootfs, the LNS and an Ethernet link layer. |
| `emulation`   | [![asciicast](https://asciinema.org/a/443408.svg)](https://asciinema.org/a/443408)  | The `emulation` verb helps manage the emulation capabilities with [QEMU](https://www.qemu.org/) open source machine emulator and virtualizer. This way, developers can test their setups and algorithms without the hardware, which facilitates testing and speeds up the development process allowing for CI/CD pipelines.  Emulation boots the same SD card image produced by previous commands and including the colcon workspace, providing a unified development approach. |
| `platform`  | [![asciicast](https://asciinema.org/a/443410.svg)](https://asciinema.org/a/443410)  | The `platform` verb helps reports Vitis platform enabled in the firmware deployed in the colcon workspace.  |
| `mkinitramfs`  | [![asciicast](https://asciinema.org/a/443412.svg)](https://asciinema.org/a/443412)  | The `mkinitramfs` verb creates compressed cpio initramfs (ramdisks). These can then be used to back up the current rootfs or to create dom0less VMs in Xen easily.  |
| `mount` / `umount`  | [![asciicast](https://asciinema.org/a/443414.svg)](https://asciinema.org/a/443414)  | The `mount` and `umount` verbs help mount/umount the raw SD card image produced by previous steps. This way, developers can easily access the embedded rootfs directly, across the various partitions of the raw image (e.g. as in the case of multi-VMs in Xen).  |


### Quality Declaration

No quality is claimed according to [REP-2004](https://www.ros.org/reps/rep-2004.html).
