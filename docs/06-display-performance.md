# 显示、性能与镜像

## 逻辑界面与物理视频分开判断

本机历史物理模式3840×2160/60Hz，正常逻辑界面1920×1080、density320。原厂播放器可经Realtek通道输出4K，逻辑1080p不等于视频只能1080p。放大逻辑桌面以“开启4K”会改变布局与负载，通常不能解决视频问题。

只读观察：

```sh
adb -s "$TV_ENDPOINT" shell wm size
adb -s "$TV_ENDPOINT" shell wm density
adb -s "$TV_ENDPOINT" shell settings --user 0 get secure display_density_forced
```

历史一次桌面试验后，运行时density恢复了，但重启又变640。本机后来将wm size、wm density与持久display_density_forced恢复为自己的已确认基线，再实际重启确认保持。该结果不是通用固件补丁；本项目不提供默认执行的缩放写入脚本，避免覆盖其他机器的原值。

## 4K / HDR / Dolby Vision

本机公共API声明DV/HDR10/HLG及HEVC、VP9、AV1等硬解能力。原厂播放[Dolby官方Sol Levante样片](https://github.com/DolbyLaboratories/dolby-vision-contents)有基础正常画面，Profile5/4K；素材没有音轨，不用于验收声音。

能力声明、视频像素、HDR元数据、实际面板输出和流媒体认证是不同证据。没有取得Widevine安全等级，不写L1；Profile5通过不能外推Profile7/FEL。官方YouTube的某次4K60素材是SDR，4K标签不证明HDR或Dolby Vision。

## 卡顿诊断

一次只改一个变量。保持相同视频与区间，记录分辨率、fps、编码、网络速度、缓冲与区间掉帧：用掉帧增量除以帧数增量，不能把开播与操作期间累计值当稳态。测试期间保持遥控器操作条件一致。

优先按需停止自己新增且当前不用的服务；保留硬件设置、媒体、输入、网络、账号、Play与必要代理组件。不用通用“卸载所有厂商包”名单。轻量桌面不保证4K不卡，原生桌面也不保证没有推荐。

## scrcpy

[官方scrcpy](https://github.com/Genymobile/scrcpy)可辅助终端调试，但这台厂商视频路径可能黑屏、冻结或视频区域不入普通抓图。既有调试没有把完整镜像认定为稳定可用。可以尝试较低镜像分辨率/帧率，终端与物理画面仍正常时，无需为了镜像修改驱动或关闭HDR。

性能测试可能有声音。夜间诊断先明确静音并记录原值，测试后恢复；未经确认不做可能播放开机音的物理重启。
