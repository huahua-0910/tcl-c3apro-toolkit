# Google 服务与原生桌面恢复

目标是恢复固件已有组件及正常引导，不是用第三方包替换驱动或伪造Google认证。先完成 [只读检查与备份](01-quickstart.md)。

## 按状态选择路径

| 状态 | 如何理解 | 下一步 |
| --- | --- | --- |
| package missing | 固件未提供、包名不同或查询权限不足 | 核实系统；不批量下载GMS拼装。 |
| installed=false | 对该用户未安装，不等同从固件删除 | 在确认系统仍保留原包后评估install-existing。 |
| hidden=true | 包被用户级策略隐藏 | 普通pm enable通常不能解除；见下方进阶流程。 |
| enabled=2/3/4 | 包被停用 | 记录原值后可正常pm enable，再读回；不同时清数据。 |
| Home在线失败 | 网络有效不等于Google初始化完成 | 按正常初始化/网络分支排查。 |
| 已经可用 | 无需修复 | 保留账号、代理、系统组件与正常默认HOME。 |

`profiles/c3apro-api34.json` 保存本机历史4项核心与11项原生组件名单。固定名单仅供核对，不是对所有Google包进行批量enable/unhide的命令。后台服务没有桌面图标也可能完全正常。

## 已存在包的普通恢复

只有确认包在系统中、当前用户为0时，才能按本机实际需要使用：

```sh
adb -s "$TV_ENDPOINT" shell cmd package install-existing --user 0 PACKAGE_NAME
adb -s "$TV_ENDPOINT" shell pm enable --user 0 PACKAGE_NAME
adb -s "$TV_ENDPOINT" shell dumpsys package PACKAGE_NAME
```

`PACKAGE_NAME` 是需替换的占位符，不要原样执行。执行前记录installed/hidden/enabled原值。若hidden仍true，不要重复enable或继续尝试授予系统签名权限。

## 进阶：临时设备所有者解除隐藏

历史单机曾通过本地testOnly DPC，用Android公开 `DevicePolicyManager.setApplicationHidden` 解除15项隐藏，再正常撤销管理身份。普通shell的 `pm unhide` 曾因缺少MANAGE_USERS被拒绝；开启ADB不会改变这个权限边界。[Android管理API](https://developer.android.com/reference/android/app/admin/DevicePolicyManager#setApplicationHidden(android.content.ComponentName,%20java.lang.String,%20boolean))

本仓库提供重构后的 `android/google-policy` 实验源码，固定白名单、无联网/服务/开机接收器/任意shell。每个包第一次修改前保存hidden原值，恢复按实际原值处理，不假定所有包原来都隐藏。公开版尚未在设备运行，因此不作为普通用户的一键功能，也不随首版Release分发DPC APK。

采用此路径前，使用者需要明确接受临时整机管理身份，以及登录账号/用户配置可能使正常授权被拒绝。已有账号导致拒绝时，停止；账号移除、清数据或重置均是单独决策，不能作为脚本补救步骤。项目不提供绕过账号条件或恢复出厂脚本。[Android开发测试设置](https://developer.android.com/work/dpc/dedicated-devices/cookbook#development-setup)

进阶执行顺序：

1. 保存固定名单状态、原HOME、设备策略/限制和备份服务状态到私人目录；将本地输出人工复核，别直接公开dumpsys。
2. 按 [构建说明](07-build.md)自行编译，核验testOnly、包名、白名单、无联网权限。用户0安装：`adb -s "$TV_ENDPOINT" install --user 0 -t dist/google-policy-0.1.0.apk`。
3. 用户明确同意本次管理实验后，正常执行 `adb -s "$TV_ENDPOINT" shell dpm set-device-owner --user 0 io.github.huahua0910.c3apro.policy/.LocalAdmin`。系统拒绝则停止，读回是否残留活动管理员。
4. **先做无隐藏修改的授予—撤销往返。** 正常testOnly撤销命令为 `adb -s "$TV_ENDPOINT" shell dpm remove-active-admin --user 0 io.github.huahua0910.c3apro.policy/.LocalAdmin`。核对owner/admin、限制、备份服务与基线；不一致则停，不进行下一步。
5. 只有往返确认后才重新正常授权，在电视工具UI按组解除隐藏、独立读回。失误时在身份撤销前使用“恢复保存的原始隐藏状态”。基线保存在工具私有目录；卸载或清数据会丢失它。保留操作前独立记录的包状态，不把工具私有文件当成已经导出的备份。
6. 通过工具撤销按钮或正常testOnly命令撤销，独立核对无owner/admin及原系统状态后才考虑卸载。正常撤销失败时保留工具与记录，停止扩展变更；不可先卸载把恢复入口丢掉。

状态检查可用 `adb ... shell dpm list-owners`、`adb ... shell dumpsys device_policy`、`adb ... shell bmgr enabled`；后两者可能含私人信息，只在本地检查。注册/撤销可能影响系统备份与限制，不承诺隐藏标志备份能够覆盖这些副作用。重构版DPC没有自动恢复整机策略的能力。

## 正常初始化与联网分支

历史固件的Google设置向导在全局VPN下发生网络匹配失败：它保存默认活动网络，但另一个NetworkRequest默认要求NOT_VPN。临时只将设置向导排除出VPN、让规则真正重新生效后，向导正常推进；完成后恢复完整VPN覆盖，Home/Play继续可用。

这是本机特定诊断，**不是通用Google服务绕过VPN指南**。复现时先对比实际活动网络/UID覆盖与错误，而不是盲改代理、DNS或大量排除Google包。本项目不附节点与订阅，也不修改服务端配置。

正常引导中的“约两分钟”未必准确：历史一次结束等待接近28分钟。记录日志并等待系统推进，不通过ADB写 `tv_user_setup_complete` 或 `device_provisioned` 假装完成。若卡住需要诊断，保持第一份失败；只做有因果依据的单变量对照。

## 设为原生桌面

Google Home已安装、hidden=false、enabled=0/1、未suspend，且正常引导完成后：

```sh
python3 tools/tvkit.py --serial "$TV_ENDPOINT" home \
  --component com.google.android.apps.tv.launcherx/.home.HomeActivity
python3 tools/tvkit.py --serial "$TV_ENDPOINT" home \
  --component com.google.android.apps.tv.launcherx/.home.HomeActivity --apply
```

工具保存原HOME，不启停其他包。完成后实按Home键、检查遥控焦点、Play目录和网络仍可用。Google原生主页包含推荐/赞助内容，不是无广告桌面。回退见 [恢复说明](05-rollback.md)。
