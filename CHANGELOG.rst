^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package colcon-hardware-acceleration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

0.5.1 (2022-03-24)
------------------
* Release 0.5.1
* Add publish-python.yaml

0.5.0 (2022-03-24)
------------------
* Release 0.5.0
* Add copyright and spell check tests
* Update stdeb.cfg
* Drop README.rst
* Advertise colcon_core.extension_point entry point for subverb
* Fix typo

0.4.0 (2022-02-15)
------------------
* Release 0.4.0
* Avoid harcoding ROS default installation

0.3.0 (2021-11-23)
------------------
* Improve CHANGELOG subitems in 0.1.0
* Add spanish language support
* Describe embedded capablities integrated in colcon-hardware-acceleration 0.2.0
* Avoid hardcoding ROS 2 workspace destination
* Create common ROS 2 script on-the-go

0.2.0 (2021-10-08)
------------------
* Enhance README demonstrating some of the capabilities
* Add no quality declaration according to REPs
* Check that rootfs exists after selection
* Fixes in run() primitive used throughout subverbs

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
