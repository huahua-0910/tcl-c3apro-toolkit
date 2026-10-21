# 快速开始

先让调试可用，再决定要改什么。以下操作针对自己的设备；电脑与电视处于可信局域网。

## 1. 电脑准备

macOS 可通过 Homebrew 安装：

```sh
brew install --cask android-platform-tools
adb version
python3 --version
```

只做终端调试不必安装或运行scrcpy；需要镜像时再选装 `brew install scrcpy`。macOS 的 `python3 --version` 需要为3.10或更高；缺少时可用 `brew install python`。未安装Homebrew时先参照其[官网](https://brew.sh/)安装，或直接使用Google工具包。Windows/Linux 可以直接使用 [Google Platform Tools](https://developer.android.com/tools/releases/platform-tools)；Python 工具用标准库，无额外pip依赖。Windows若命令为 `py -3` 而不是python3，请相应替换文档中的Python命令前缀。

下载本仓库后在仓库根目录执行命令。可以直接使用GitHub下载ZIP，也可克隆以便后续更新：

```sh
git clone https://github.com/huahua-0910/tcl-c3apro-toolkit.git
cd tcl-c3apro-toolkit
```

## 2. 打开开发者与无线调试

第一次还没有ADB时，从[设置入口发行页](https://github.com/huahua-0910/tcl-c3apro-toolkit/releases/tag/v0.1.0)下载 `settings-hub-0.1.0.apk` 与 `SHA256SUMS.txt`。macOS本地核对：

```sh
shasum -a 256 ./settings-hub-0.1.0.apk
```

将结果与同页SHA256SUMS中APK一行比对；Linux使用 `sha256sum`，Windows可用PowerShell `Get-FileHash -Algorithm SHA256`。这验证文件一致性，不代替信任发布者或阅读源码。将APK复制到U盘，用电视已有的文件管理/安装入口打开，只为该来源允许安装，然后在应用列表打开“设置与调试”。**成功判断：能用遥控器看到并进入系统开发者页面。** 若系统禁止本地安装或页面被保护，就停止在这个分支，不假定ADB已开启。

本机“安卓版本”连按进入 Android 14 图标页面，是彩蛋入口，不是开发者选项。如果关于页面没有构建号，先用原系统允许的 U 盘 APK 安装方式安装本项目设置入口，或用可信 Activity Launcher 查找系统开发者页面。

本次历史固件的开发者目标是 `com.android.tv.settings/.system.development.DevelopmentActivity`；标准 action 是 `android.settings.APPLICATION_DEVELOPMENT_SETTINGS`。若有 USB/无线调试开关，通过正常界面开启。设置入口只是打开已有页面，遇到权限拒绝、页面不存在时记录情况，不会取得 shell/root。

ADB 已可连接时才可以执行：

```sh
adb -s "$TV_ENDPOINT" shell am start -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS
```

不要用“先 adb install 入口工具”来解释第一次开启 ADB，那会循环依赖。

## 3. 配对与连接

在电视无线调试页面打开“使用配对码配对”，在自己电脑本地输入配对码：

以下终端示例使用macOS/Linux的bash或zsh。先在当前终端输入两个端点，不把真实地址写入仓库：

```sh
printf '无线调试主页面的连接 IP:端口：'
read -r TV_ENDPOINT
printf '配对弹窗中的配对 IP:端口：'
read -r TV_PAIR_ENDPOINT
adb pair "$TV_PAIR_ENDPOINT"
adb connect "$TV_ENDPOINT"
adb -s "$TV_ENDPOINT" get-state
```

配对码只在ADB提示时本地输入。**成功判断：pair提示成功、connect提示connected/already connected，get-state返回device。** offline、unauthorized或端点为空时先停，不进入备份/写入。PowerShell可分别用 `$TV_ENDPOINT = Read-Host '连接端点'`、`$TV_PAIR_ENDPOINT = Read-Host '配对端点'`，再执行同样的ADB命令；不要把bash的read命令复制进PowerShell。

`TV_PAIR_ENDPOINT` 对应配对弹窗端点；`TV_ENDPOINT` 对应无线调试主页面的连接端点。两者端口通常不同，断网/重启后可能变化。无需在聊天或 issue 报配对码。只有固件明确开启传统网络调试时才使用该页面显示的传统端口，不扫描网段猜地址。

## 4. 只读检查

```sh
python3 tools/tvkit.py --serial "$TV_ENDPOINT" inspect --out state/inspect-before.json
```

确认型号、API、ABI、`current_user`、当前桌面和 Google 状态。**成功判断：命令退出为0，JSON已保存，型号C3APRO、API34，当前用户为0，当前HOME是实际可用的桌面。** `package_state_user=0`说明列出的包状态属于主用户；当前用户不是0时，先在设备上正常切回主用户。工具不收集账号、完整网络配置、截图或 logcat。输出仍应人工检查后再分享。当前变更工具只接受 `C3APRO / API 34 / 当前用户0`。

## 5. 备份本轮会动的包

```sh
python3 tools/tvkit.py --serial "$TV_ENDPOINT" backup \
  --package com.google.android.apps.tv.launcherx \
  --package com.google.android.tungsten.setupwraith
```

其他待替换应用也用重复的 `--package` 指定。命令复制全部能读取的 base/split APK，并核对设备 SHA-256；先查看 manifest 是否 `PASS_APK_COPY_AND_DIGEST`。首次失败会留下 `FAILED_PARTIAL_BACKUP`，不是完整备份。原桌面包名从实际体检/固件确认，另行备份。

`state/inspect-before.json`保留的是本机检查结果；以后不要在第一次变更后把它覆盖为新的“操作前”基线。下一轮用不同文件名保存。

APK 备份不包含私有账号和应用数据。要更新应用时同时在应用内导出可用的设置；导出不可用时不要假定已有完整回档。

接下来按 [Google 恢复分支](03-google-recovery.md)处理；已正常可用的组件保持现状。结束时执行 `adb disconnect "$TV_ENDPOINT"`，按需要在电视关闭无线调试。仅断开连接不会关闭调试开关或撤销已配对电脑。

## 不连接电视的自检

只想确认项目下载完整，可直接运行：

```sh
python3 -m unittest discover -s tests -v
python3 tools/audit_public.py
```

测试会用临时目录与假ADB演练，不使用真实ADB或电视。Git克隆会扫描暂存区；ZIP解压会自动扫描源文件树；未安装Git时，两个Git专用测试会跳过，不影响其他自检；原生Windows会跳过POSIX命令行演练，可在WSL补测。成功时测试为OK、扫描0 findings。设备上的安装、焦点、声音和真实播放仍需要另行验收。
