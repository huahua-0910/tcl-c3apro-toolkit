# 快速开始

先让调试可用，再决定要改什么。以下操作针对自己的设备；电脑与电视处于可信局域网。

## 1. 电脑准备

macOS 可通过 Homebrew 安装：

```sh
brew install --cask android-platform-tools
brew install scrcpy
adb version
python3 --version
```

只做终端调试不必运行 scrcpy。Windows/Linux 可以直接使用 [Google Platform Tools](https://developer.android.com/tools/releases/platform-tools)；Python 工具用标准库，无额外 pip 依赖。

下载本仓库后在仓库根目录执行命令。可以直接使用GitHub下载ZIP，也可克隆以便后续更新：

```sh
git clone https://github.com/huahua-0910/tcl-c3apro-toolkit.git
cd tcl-c3apro-toolkit
```

## 2. 打开开发者与无线调试

本机“安卓版本”连按进入 Android 14 图标页面，是彩蛋入口，不是开发者选项。如果关于页面没有构建号，先用原系统允许的 U 盘 APK 安装方式安装本项目设置入口，或用可信 Activity Launcher 查找系统开发者页面。

本次历史固件的开发者目标是 `com.android.tv.settings/.system.development.DevelopmentActivity`；标准 action 是 `android.settings.APPLICATION_DEVELOPMENT_SETTINGS`。若有 USB/无线调试开关，通过正常界面开启。设置入口只是打开已有页面，遇到权限拒绝、页面不存在时记录情况，不会取得 shell/root。

ADB 已可连接时才可以执行：

```sh
adb -s "$TV_ENDPOINT" shell am start -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS
```

不要用“先 adb install 入口工具”来解释第一次开启 ADB，那会循环依赖。

## 3. 配对与连接

在电视无线调试页面打开“使用配对码配对”，在自己电脑本地输入配对码：

```sh
adb pair "$TV_PAIR_ENDPOINT"
adb connect "$TV_ENDPOINT"
adb devices -l
```

`TV_PAIR_ENDPOINT` 对应配对弹窗端点；`TV_ENDPOINT` 对应无线调试主页面的连接端点。两者端口通常不同，断网/重启后可能变化。无需在聊天或 issue 报配对码。只有固件明确开启传统网络调试时才使用该页面显示的传统端口，不扫描网段猜地址。

## 4. 只读检查

```sh
python3 tools/tvkit.py --serial "$TV_ENDPOINT" inspect
```

确认型号、API、ABI、当前桌面和 Google 状态。工具不收集账号、完整网络配置、截图或 logcat。输出仍应人工检查后再分享。当前变更工具只接受 `C3APRO / API 34 / 当前用户0`。

## 5. 备份本轮会动的包

```sh
python3 tools/tvkit.py --serial "$TV_ENDPOINT" backup \
  --package com.google.android.apps.tv.launcherx \
  --package com.google.android.tungsten.setupwraith
```

其他待替换应用也用重复的 `--package` 指定。命令复制全部能读取的 base/split APK，并核对设备 SHA-256；先查看 manifest 是否 `PASS_APK_COPY_AND_DIGEST`。首次失败会留下 `FAILED_PARTIAL_BACKUP`，不是完整备份。原桌面包名从实际体检/固件确认，另行备份。

APK 备份不包含私有账号和应用数据。要更新应用时同时在应用内导出可用的设置；导出不可用时不要假定已有完整回档。

接下来按 [Google 恢复分支](03-google-recovery.md)处理；已正常可用的组件保持现状。结束后断开 ADB，按需要关闭无线调试。
