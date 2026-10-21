# 来源与设计依据

核对日期：2026-10-21。上游功能、版本和政策会变化；下载时重新核对发行页面。第一方资料能说明API与项目行为，不能代替本机验收。

| 内容 | 第一方来源 |
| --- | --- |
| ADB/配对/用户范围 | [Android ADB文档](https://developer.android.com/tools/adb)、[Platform Tools](https://developer.android.com/tools/releases/platform-tools) |
| 开发者设置导航 | [Settings API](https://developer.android.com/reference/android/provider/Settings#ACTION_APPLICATION_DEVELOPMENT_SETTINGS) |
| 设备所有者开发路径 | [Dedicated devices cookbook](https://developer.android.com/work/dpc/dedicated-devices/cookbook#development-setup) |
| hidden策略 | [DevicePolicyManager](https://developer.android.com/reference/android/app/admin/DevicePolicyManager#setApplicationHidden(android.content.ComponentName,%20java.lang.String,%20boolean)) |
| 网络NOT_VPN | [Android14 NetworkCapabilities源码](https://android.googlesource.com/platform/packages/modules/Connectivity/+/refs/tags/android-14.0.0_r1/framework/src/android/net/NetworkCapabilities.java) |
| HDR能力 | [Display.HdrCapabilities](https://developer.android.com/reference/android/view/Display.HdrCapabilities) |
| YouTube HDR | [YouTube帮助](https://support.google.com/youtube/answer/7126552?hl=zh-Hans) |
| Dolby素材 | [Dolby Laboratories内容仓库](https://github.com/DolbyLaboratories/dolby-vision-contents) |
| scrcpy | [Genymobile/scrcpy](https://github.com/Genymobile/scrcpy) |
| 代理客户端 | [chen08209/FlClash](https://github.com/chen08209/FlClash) |
| 夸克TV | [官网](https://pan.quark.cn/)、[版本接口](https://pan.quark.cn/api/client_version) |
| 夸克官方接口区别 | [官方网盘Skill](https://github.com/quark-clouddrive/quarkclouddrive_offical/blob/main/README.md)；不能外推任意TV播放器授权 |
| B站官方 | [应用下载](https://app.bilibili.com/)、[国际站](https://www.bilibili.tv/en/download) |
| newBV | [Frost819/newBV](https://github.com/Frost819/newBV) |
| AirPlay接收器 | [jqssun/android-airplay-server](https://github.com/jqssun/android-airplay-server) |
| Kodi | [官方Android下载](https://kodi.tv/download/android/) |
| OpenList夸克维护范围 | [驱动文档](https://doc.oplist.org/guide/drivers/quark) |
| 同型号开发者页面线索 | [27c3apro_kvm固定源码](https://github.com/ldbfpiaoran/27c3apro_kvm/blob/4d5ab914c641d11b257e0ca929e75e235303f739/app/src/main/java/com/codex/tclusbadbhelper/MainActivity.java#L317-L341)；不采用其root/KVM实验脚本 |

TCL电子说明书曾用于确认产品与系统菜单，但不包含已证实的ADB开启说明；本项目不转载该PDF。找不到构建号时不把其他TCL海外型号的按键序列说成本机通用方法。
