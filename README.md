# TCL 27C3A Pro Android TV Toolkit

把内置安卓整理成好用的电视系统：恢复已有的 Google 组件、使用原生 Google TV 桌面、保留硬件设置，并让每次调整都有记录和回退路径。

这是 **27C3A Pro 内置 Android 系统**的社区指南与小工具，不是 TCL 固件、Google 认证 ROM 或刷机包。中文优先，面向普通用户与协作智能体。

**工具与指南 0.1.1；设置入口 APK 0.1.0**：整理自一台 `C3APRO / Android 14 / API 34 / armeabi-v7a` 的实际调试。公开版工具已重构，设备执行仍需使用者验证；历史实测与公开工具的验证范围分开记录。

## 从这里开始

1. [快速开始](docs/01-quickstart.md)：准备 ADB、打开开发者入口、配对、检查、备份。
2. [Google 服务与原生桌面](docs/03-google-recovery.md)：按 missing / hidden / disabled / setup / network 分支处理。
3. [应用选择与安装](docs/04-apps.md)：官方客户端、ARM32、免费投屏与第三方替代。
4. [回退与故障排查](docs/05-rollback.md)：恢复默认桌面、APK 回装及备份的实际边界。

只想快速找设置：在 [设置入口发行页](https://github.com/huahua-0910/tcl-c3apro-toolkit/releases/tag/v0.1.0) 下载本项目的 `settings-hub-0.1.0.apk`，用系统已有的本地 APK 安装方式安装，再打开“设置与调试”。它只导航到原系统页面，没有联网、后台服务或设备管理权限。入口是否存在及允许启动取决于固件，APK 不能凭空开启 ADB。

## 能做什么

| 内容 | 提供的能力 |
| --- | --- |
| 只读体检 | 型号/API/ABI、当前 HOME、缩放、固定 Google 名单的用户级包状态 |
| APK 备份 | 备份所选应用的 base/split APK，逐件核对设备与本地 SHA-256 |
| 桌面切换 | 默认预览；检查目标、保存原 HOME、显式执行、失败时尝试恢复 |
| 设置入口 | 无权限 Android TV 应用，遥控器打开开发者/系统/网络/关于页面 |
| Google 隐藏恢复 | 固定 4+11 项白名单、保存原 hidden 值的实验 DPC 源码；单列进阶流程 |
| 文档与协作 | 适配说明、故障决策、应用来源、人工验收和智能体执行规则 |

不附 Google/TCL/第三方 APK、账号、代理订阅、签名私钥或原始设备备份。Google 核心组件优先恢复本机已有包；这些组件不在固件里时，本项目不把安装几份 APK 当作完整 Google 认证方案。

## 最短命令路径

需要 Python 3.10+ 与 Android Platform Tools。在仓库根目录执行；先按[配对与端点输入](docs/01-quickstart.md#3-配对与连接)设置当前终端的 `TV_ENDPOINT`。连接端点来自无线调试主页面，不是配对端口。

```sh
python3 tools/tvkit.py --serial "$TV_ENDPOINT" inspect --out state/inspect-before.json
python3 tools/tvkit.py --serial "$TV_ENDPOINT" backup \
  --package com.google.android.apps.tv.launcherx \
  --package com.google.android.tungsten.setupwraith
```

`TV_ENDPOINT` 由使用者在本地设置。备份写入被 Git 忽略的 `state/`；此目录只留在自己电脑上。Google 包不存在或尚未可读取时先阅读 [恢复分支](docs/03-google-recovery.md)。

桌面切换示例（Google 正常初始化完成、包已可用，并且原默认桌面也可作为回退目标的前提下）：

```sh
python3 tools/tvkit.py --serial "$TV_ENDPOINT" home \
  --component com.google.android.apps.tv.launcherx/.home.HomeActivity
# 检查预览后，在同一命令末尾加入 --apply 执行。
```

这只设置默认 HOME，不停用其他桌面、不清数据、不写初始化标记。若固件不接受默认 HOME 设置，工具停止并尝试回退；不会继续用停用系统组件的方式强推。

## 已知结果与适用范围

历史单机上已完成：已有 Google 包解除隐藏、官方 Home/Play 基础可用、原账号及网络配置保留、主页回退往返；缩放持久修复经过一次实际重启；原厂杜比样片基础画面正常。

这不等于公开版脚本在所有固件通过。持续 4K60、所有 HDR Profile、完整 AirPlay 镜像/声音、手机 Cast、实体语音仍有未验收部分。详见 [兼容与验收矩阵](docs/02-compatibility.md)。

## 项目导航

| 文档 | 何时阅读 |
| --- | --- |
| [显示、性能与镜像](docs/06-display-performance.md) | 比例异常、4K卡顿、scrcpy黑屏 |
| [构建 Android 工具](docs/07-build.md) | 自己编译设置入口或研究 DPC |
| [公开化与隐私](docs/08-privacy.md) | 提交日志、截图、贡献或准备发布 |
| [来源与设计依据](docs/09-sources.md) | 查看第一方文档及上游项目 |
| [首次使用复核](docs/12-first-use-review.md) | 查看0.1.1修复的问题与模拟演练范围 |
| [当前进度](docs/10-status.md) | 查看完成项、局限和下一步 |
| [贡献说明](CONTRIBUTING.md) | 提交固件兼容结果或修改 |
| [AGENTS.md](AGENTS.md) | 让智能体辅助维护、诊断与操作 |

欢迎提交脱敏后的同型号适配结果。项目原创代码与文档采用 [MIT License](LICENSE)，上游应用和厂商资料遵循各自许可。
