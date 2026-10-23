# Redmi Note 10 5G (camellia)

camellia is the Redmi Note 10 5G with the MediaTek MT6833 SoC. This is an
independent work-in-progress port. It is not a supported or bootable device
configuration yet.

| Repository | Maintainer | State |
| --- | --- | --- |
| UniXNU `feature/camellia-bringup` | [stanveyjiang](https://github.com/stanveyjiang) | XNU entry reached; early page tables in progress |
| uefi-camellia | stanveyjiang | UEFI, UniXNU payload and framebuffer bring-up |

## State

| Stage | State |
| --- | --- |
| `LK` to a project-built Linux kernel | works |
| Minimal initramfs and linear DRM framebuffer | works |
| `uefi_jump` from Linux to UEFI | works |
| UEFI graphics and UniXNU menu | works |
| 64 MiB RamDisk payload | works |
| DarwinBoot handoff and MMU-off entry | works |
| XNU `_start_first_cpu` | entry reached |
| XNU bootstrap page tables | in progress; first L2 fill does not converge on hardware |
| XNU MMU and iOS userland | not reached |

The current boot path is unusual because LK does not accept a self-contained
UEFI image directly on this device:

```text
LK
-> project Linux kernel
-> minimal initramfs
-> linear DRM framebuffer
-> uefi_jump.ko
-> UEFI
-> UniXNU
-> DarwinBoot
-> XNU
```

No Android userland, Magisk module or `service.d` script is required.

## Platform facts

| Item | Value |
| --- | --- |
| SoC | MediaTek MT6833 |
| Panel | 1080 x 2400, 90 Hz |
| Framebuffer | scattered IOMMU-backed 4 KiB physical pages |
| Pixel layout | 32 bpp BGRA in memory (`PixelBlueGreenRedReserved8BitPerColor` in GOP terms) |
| UEFI payload | 64 MiB raw RamDisk image |
| UFS | vendor `11270000.ufshci`; native UFS driver not implemented |
| Touch | FocalTech FT8722 on SPI4; native driver not implemented |

## Current blocker

XNU executes the Mach-O entry and reaches the first bootstrap L2 mapping fill.
An observation-only probe shows that the post-fill `subs` does not set the
zero flag on hardware. Under QEMU with the documented virtual base, physical
base and 80 MiB window, the observed values are:

```text
x5  = 0x11
x6  = 0x11
x24 = 0x02278000
```

That produces `x5 = 0` and should take the completion branch. The hardware
result differs, so the next work item is to inspect the runtime boot arguments
and fixed-window state without bypassing page-table entries.

Forced branch, enlarged page tables and hard-coded zero counts are diagnostic
only. They are not accepted as fixes.

## Build and boot status

The current branch is for development and diagnostics. It does not contain a
release payload, kernel, boot image or proprietary device data. A buildable,
supported configuration will be documented only after the XNU page-table and
MMU stages pass on hardware.

## Maintenance

The maintainer owns this port and its release decisions. UniXNU documents the
work in progress; it does not claim that the device boots XNU or iOS.
