^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package colcon_acceleration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
0.1.0 (2021-09-07)
------------------
* Include initial capabilities. Verbs available initially:
  * board                 Report the board supported in the deployed firmware
  * emulation             Manage emulation capabilities
  * hls                   Vitis HLS capabilities management extension
  * hypervisor            Configure the Xen hypervisor
  * linux                 Configure the Linux kernel
  * list                  List supported firmware for hardware acceleration
  * mkinitramfs           Creates compressed cpio initramfs (ramdisks)
  * mount                 Mount raw images
  * platform              Report the platform enabled in the deployed firmware
  * select                Select an existing firmware and default to it
  * umount                Umount raw images
  * v++                   Vitis v++ compiler wrapper
  * version               Report version of the tool
* Support for various boards