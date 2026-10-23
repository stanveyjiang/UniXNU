# Redmi Note 10 5G（camellia）

camellia 是搭载联发科 MT6833 的 Redmi Note 10 5G。这个移植目前独立维护，
仍是进行中的开发分支，不是受支持的可启动配置。

| 仓库 | 维护者 | 状态 |
| --- | --- | --- |
| UniXNU `feature/camellia-bringup` | [stanveyjiang](https://github.com/stanveyjiang) | 已到 XNU 入口，早期页表进行中 |
| uefi-camellia | stanveyjiang | UEFI、UniXNU payload 和显示 bring-up |

## 状态

| 阶段 | 状态 |
| --- | --- |
| `LK` 启动项目自建 Linux 内核 | 工作 |
| 最小 initramfs 与线性 DRM framebuffer | 工作 |
| `uefi_jump` 从 Linux 进入 UEFI | 工作 |
| UEFI 显示和 UniXNU 菜单 | 工作 |
| 64 MiB RamDisk payload | 工作 |
| DarwinBoot 交接与 MMU-off 入口 | 工作 |
| XNU `_start_first_cpu` | 已进入 |
| XNU bootstrap 页表 | 进行中；真机第一次 L2 填充没有自然收敛 |
| XNU MMU 和 iOS 用户态 | 未到达 |

本设备不能由 LK 直接启动自包含 UEFI 镜像，因此当前启动链为：

```text
LK
-> 项目自建 Linux 内核
-> 最小 initramfs
-> 线性 DRM framebuffer
-> uefi_jump.ko
-> UEFI
-> UniXNU
-> DarwinBoot
-> XNU
```

该路径不依赖 Android 用户态、Magisk 模块或 `service.d`。

## 平台数据

| 项目 | 值 |
| --- | --- |
| SoC | MediaTek MT6833 |
| 面板 | 1080 x 2400，90 Hz |
| Framebuffer | IOMMU 映射的散页，4 KiB 物理页 |
| 像素布局 | 内存中 32 bpp BGRA（GOP 的 `PixelBlueGreenRedReserved8BitPerColor`） |
| UEFI payload | 64 MiB 原始 RamDisk 镜像 |
| UFS | 厂商控制器 `11270000.ufshci`；尚未实现原生驱动 |
| 触控 | SPI4 上的 FocalTech FT8722；尚未实现原生驱动 |

## 当前阻塞

XNU 已执行 Mach-O 入口并进入第一段 bootstrap L2 映射填充。不改变控制流的
探针显示，填充后的 `subs` 在真机上没有置零标志。QEMU 使用文档中的虚拟基址、
物理基址和 80 MiB 窗口时得到：

```text
x5  = 0x11
x6  = 0x11
x24 = 0x02278000
```

因此 `x5` 应归零并进入完成分支，但真机结果不同。下一项工作是在不跳过页表项的
前提下检查运行时 boot args 和固定窗口状态。

强制跳转、扩大页表或硬编码计数归零都只能用于诊断，不能作为修复。

## 构建与启动状态

当前分支只用于开发和诊断，不包含发布 payload、内核、boot 镜像或厂商设备数据。
只有 XNU 页表与 MMU 阶段在真机通过后，才会补充可复现的受支持构建配置。

## 维护

维护者拥有移植和发布决定。UniXNU 仅记录进行中的工作，不宣称该设备已经启动
XNU 或 iOS。
