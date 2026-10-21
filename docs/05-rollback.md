# 回退与故障排查

备份分层：APK副本、包状态、默认HOME与设置原值是不同恢复材料；这些都不是完整系统镜像。普通ADB通常不能备份应用私有数据库、账号令牌和服务器状态。

## 默认桌面回退

公开版工具仅修改默认HOME，每次apply生成单独的 `state/home-*.json`，包含原HOME、目标及本地设备绑定摘要。工具不会为了切桌面自动停用其他包。执行前原HOME必须是可用的HOME候选；系统解析器、不可用或尚未完成引导的桌面不作为自动回退目标，此时先在系统设置里确认一个可用默认桌面。

变更失败时会保留首次错误并尝试恢复原HOME；`rollback=FAILED_REQUIRES_LOCAL_REVIEW` 必须人工处理，不能继续批量执行。

操作前先记下工具预览中的 `before_home`，并保留至少一个可用原桌面。使用工具输出的真实receipt路径替换下面的 `state/home-TRANSACTION.json`；它是示意文件名，不是仓库自带文件：

```sh
python3 tools/tvkit.py --serial "$TV_ENDPOINT" restore-home --receipt state/home-TRANSACTION.json
python3 tools/tvkit.py --serial "$TV_ENDPOINT" restore-home --receipt state/home-TRANSACTION.json --apply
```

成功判断：返回 `PASS_HOME_RESOLUTION`；实按Home键进入预期桌面，并检查方向键与常用应用。工具的通过状态只验证默认解析，`physical_home_key=NOT_RUN`需要人工补验。

磁盘在设备变更后故障时，工具仍尝试回退，但JSON可能停留在PREPARED/APPLYING。终端会报告原始错误、rollback和receipt_write_failures，不能把旧JSON当成最终状态。先用 `inspect` 和物理Home键确认，再恢复存储；不要重跑apply来掩盖失败。若回执不可读，使用先前保存的 `before_home`，按本节末尾的手动入口恢复。

restore生成新事务，不覆盖旧记录；设备绑定不一致、原桌面不可用或API不符就停。恢复默认解析不等于已验证按Home键、焦点和重启效果，这些需要实机操作。

如果没有可读receipt，可以在系统默认应用设置里选择原桌面。ADB仍连接且原包/组件可用时，明确把本地记录的组件填入变量：

```sh
printf '输入事前记录的原HOME package/activity：'
read -r ORIGINAL_HOME
adb -s "$TV_ENDPOINT" shell cmd package set-home-activity --user 0 "$ORIGINAL_HOME"
adb -s "$TV_ENDPOINT" shell cmd package resolve-activity --brief --user 0 -a android.intent.action.MAIN -c android.intent.category.HOME
```

比对返回组件，再实按Home键。此为绕过损坏本地回执的手动恢复步骤，没有自动保护或回执；用户0、包状态和组件必须事先核实。历史原设备有LTvLauncher，但其他用户不能假定同一个第三方桌面已经安装。

## APK回装

查看 `state/backup-*/manifest.json`，核对状态、包名和每件文件摘要。单APK正常 `install --user 0 -r`，split按同一包完整集合 `install-multiple --user 0 -r`。只使用自己备份的同签名、系统允许的版本。Android拒绝降级时停止，不以卸载清数据“恢复”。

新增普通应用可在系统设置里卸载。直接ADB卸载不是所有者策略回退；实验DPC应先完成正常撤销并确认无owner/admin，保留需要的恢复材料后再卸载。

## enabled / installed / hidden分别恢复

原值取自操作前的inspect或所选包backup manifest，不能只看现在图标是否出现。恢复enabled时，**只选与原数字对应的一条**，不要顺序执行整张表：

| 原enabled | 用户0的正常命令（PACKAGE_NAME需替换为本人目标包） |
| --- | --- |
| 0，默认 | `adb -s "$TV_ENDPOINT" shell pm default-state --user 0 PACKAGE_NAME` |
| 1，显式开启 | `adb -s "$TV_ENDPOINT" shell pm enable --user 0 PACKAGE_NAME` |
| 2，停用 | `adb -s "$TV_ENDPOINT" shell pm disable --user 0 PACKAGE_NAME` |
| 3，用户停用 | `adb -s "$TV_ENDPOINT" shell pm disable-user --user 0 PACKAGE_NAME` |
| 4，停用至使用 | `adb -s "$TV_ENDPOINT" shell pm disable-until-used --user 0 PACKAGE_NAME` |

这些名称与[Android14命令实现](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-14.0.0_r1/services/core/java/com/android/server/pm/PackageManagerShellCommand.java)一致，固件仍可能限制调用；命令被拒绝就停止，不增加权限。逐项读回User 0状态。恢复enabled不恢复installed/hidden，也不恢复账户与应用私有状态。

若本轮用install-existing把原installed=false变成true，反向用户卸载可能影响刚生成的数据、账号与组件依赖；不能承诺它是完整可逆操作，不提供批量反向卸载名单。

**DPC的隐藏状态恢复窗口在管理身份撤销之前。** 希望撤回时先用工具恢复保存的hidden原值，再撤销身份。撤销后若又登录了账号，Android可能拒绝重新授权；有一份旧hidden记录不代表普通ADB就能恢复它。不自动移除账号来重获身份，也不把清除所有者、初始化和服务端状态描述为完整回档。

## 常见故障

| 现象 | 首先检查 |
| --- | --- |
| adb offline / unauthorized | 当前端点、无线调试状态、电视授权；不将旧配对端口当连接端口。 |
| App无法安装 | ABI、版本、签名、split、minSdk、用户范围；保留安装器的第一份错误。 |
| Google Home无网络、Play可用 | 正常引导状态、向导错误与实际VPN网络路径；不直接清GMS数据。 |
| Play目录超时但详情可打开 | 分辨商店目录/进程/账号与通用联网问题；只重启进程作为较小对照。清Play数据属于单独不可完整备份的变更，需使用者知情选择。 |
| pm enable后仍看不见Google包 | hidden/installed/enabled分别检查；后台组件本来就未必有图标。 |
| scrcpy黑视频但电视有画面 | 厂商SIDEband/安全视频路径，不能据此判断播放器坏或HDR不支持。 |
| 比例变大 | 读wm与持久density原值；恢复本机基线，别照抄其他固件值。 |
| 4K卡顿 | 当前编码/码率、硬解、缓冲、区间掉帧与后台负载；不从界面分辨率推断。 |

## 收尾验收

检查原账号、原有常用应用、默认HOME、代理/DNS/VPN与缩放保持预期；受控测试后恢复原音量与输入源。把媒体播放、声音、遥控、投屏、重启分别记录；有一项未测试就写NOT_RUN。测试工具不留设备所有者身份，不为追求全绿而清数据、重置或自动刷机。
