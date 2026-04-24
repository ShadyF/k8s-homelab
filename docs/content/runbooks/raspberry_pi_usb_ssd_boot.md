---
title: Raspberry Pi USB SSD boot runbook
---

# Raspberry Pi USB SSD boot runbook

This runbook records a resolved Raspberry Pi 4 USB SSD boot failure so future agents can compare similar symptoms before
assuming the SSD, USB-SATA adapter, or UAS driver is faulty.

## Resolved incident: zero-byte Pi 4 device-tree blob

### Hardware and boot context

- Raspberry Pi 4 booting Ubuntu from a Samsung 870 EVO 250GB SSD.
- USB-SATA adapter: Ugreen / ASMedia `174c:55aa`.
- The adapter enumerated on Linux as USB3 SuperSpeed with `Driver=uas`.
- Pi 4 bootloader was recent: `2026/01/09`.
- Boot order was `BOOT_ORDER=0xf14`, which means SD first, then USB.
- SSD layout used Ubuntu's Raspberry Pi labels:
  - FAT boot partition: `system-boot`
  - root partition: `writable`
- `cmdline.txt` was a single line and successfully booted without a USB storage quirk:

```text
console=serial0,115200 multipath=off dwc_otg.lpm_enable=0 console=tty1 root=LABEL=writable rootfstype=ext4 rootwait fixrtc
```

!!! warning "Do not cargo-cult the UAS quirk"
    `usb-storage.quirks=174c:55aa:u` was briefly tested, then removed. The successful boot used normal UAS. Only add a
    UAS-disable quirk if new evidence specifically points to UAS problems, such as repeated USB resets, UAS command
    failures, I/O errors, or adapter-specific kernel logs.

### Evidence that ruled out hardware and UAS

- SSD SMART status passed.
- Important SMART attributes were clean:
  - `Reallocated_Sector_Ct=0`
  - `Used_Rsvd_Blk_Cnt_Tot=0`
  - `Runtime_Bad_Block=0`
  - uncorrectable errors: `0`
  - CRC errors: `0`
- A SMART short self-test completed without error.
- A full read-only disk read completed with no I/O errors:

```text
250,059,350,016 bytes read at about 417 MB/s
```

- The ASMedia adapter stayed on USB3 SuperSpeed with `Driver=uas` during the successful read.

Conclusion: the SSD, adapter, and UAS path were not the root cause in this incident.

### Corruption indicators on the boot partition

The FAT `system-boot` partition showed signs of previous corruption:

- 662 `FSCK*.REC` files.
- Multiple zero-byte device-tree blob files.
- The Pi 4 DTB on the SSD was zero bytes:

```text
/media/shadyf/system-boot1/bcm2711-rpi-4-b.dtb
/media/shadyf/system-boot1/bcm2711-rpi-4-b.dtb.bak
```

- The known-good SD boot copy was nonzero:

```text
/boot/firmware/bcm2711-rpi-4-b.dtb  56,249 bytes
```

### Repair that fixed the boot

The zero-byte SSD Pi 4 DTB was backed up, then replaced from the known-good SD boot partition:

```shell
sudo cp /media/shadyf/system-boot1/bcm2711-rpi-4-b.dtb \
  /media/shadyf/system-boot1/bcm2711-rpi-4-b.dtb.zero-before-repair.<timestamp>

sudo cp /boot/firmware/bcm2711-rpi-4-b.dtb \
  /media/shadyf/system-boot1/bcm2711-rpi-4-b.dtb

sync
```

The repaired SSD DTB matched the known-good SD DTB:

```text
0556304e1a94ab0c3cecf27fa5619d799eeeb69e66ac3abf1bd47cce79e5039e
```

After syncing and unmounting the SSD boot partition, the Raspberry Pi booted successfully from the SSD.

## Diagnosis checklist for similar failures

When a Raspberry Pi 4 fails to boot from USB SSD, use read-only checks first:

1. Confirm whether the disk is healthy before changing boot files:

   ```shell
   sudo smartctl -a /dev/sda
   sudo smartctl -t short /dev/sda
   sudo smartctl -l selftest /dev/sda
   ```

2. Check whether the USB adapter is actually failing or only suspected:

   ```shell
   lsusb
   lsusb -t
   dmesg -T | grep -Ei 'uas|usb|reset|sda|i/o error|blk_update_request'
   ```

3. If booted from SD, inspect the SSD boot partition without repairing it first:

   ```shell
   sudo fsck.vfat -n /dev/sda1
   ```

4. Look for FAT recovery files and zero-byte firmware files:

   ```shell
   find /media/<user>/system-boot* -maxdepth 1 -name 'FSCK*.REC' | wc -l
   find /media/<user>/system-boot* -maxdepth 1 -name '*.dtb' -size 0 -ls
   ls -l /media/<user>/system-boot*/bcm2711-rpi-4-b.dtb /boot/firmware/bcm2711-rpi-4-b.dtb
   sha256sum /media/<user>/system-boot*/bcm2711-rpi-4-b.dtb /boot/firmware/bcm2711-rpi-4-b.dtb
   ```

5. Verify `cmdline.txt` is still a single line and points at the expected root filesystem:

   ```shell
   cat /media/<user>/system-boot*/cmdline.txt
   lsblk -f
   ```

## Follow-up hardening after recovery

- Confirm the running system is mounted from the SSD root partition, not the fallback SD card:

  ```shell
  findmnt /
  lsblk -f
  ```

- Confirm the adapter still uses UAS unless there is evidence to disable it:

  ```shell
  lsusb -t
  ```

- Enable periodic TRIM for the SSD:

  ```shell
  sudo systemctl enable --now fstrim.timer
  systemctl status fstrim.timer
  ```

- Check for Raspberry Pi power or throttling problems that could contribute to filesystem corruption:

  ```shell
  vcgencmd get_throttled
  ```

- Reinstall or regenerate Raspberry Pi boot files if package names match the installed Ubuntu release:

  ```shell
  sudo apt install --reinstall linux-raspi linux-firmware-raspi flash-kernel
  sudo flash-kernel
  ```

- Back up the boot partition after it is known-good.
- Watch for new `FSCK*.REC` files after future boots or kernel updates.
- After kernel or firmware updates, verify the Pi 4 DTB remains nonzero:

  ```shell
  test -s /boot/firmware/bcm2711-rpi-4-b.dtb && echo "Pi 4 DTB is present"
  ```

## Incident conclusion

The root cause was a corrupted or missing Pi 4 device-tree blob on the FAT boot partition. It was not an SSD hardware
failure, not a USB-SATA adapter failure, and not a UAS driver issue.
