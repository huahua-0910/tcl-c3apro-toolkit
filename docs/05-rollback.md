# 回退与故障排查

备份分层：APK副本、包状态、默认HOME与设置原值是不同恢复材料；这些都不是完整系统镜像。普通ADB通常不能备份应用私有数据库、账号令牌和服务器状态。

## 默认桌面回退

公开版工具仅修改默认HOME，每次apply生成单独的 `state/home-*.json`，包含原HOME、目标及本地设备绑定摘要。工具不会为了切桌面自动停用其他包。变更失败时会留下首次失败并尝试恢复原HOME；`rollback=FAILED_REQUIRES_LOCAL_REVIEW` 必须人工处理，不能继续批量执行。

使用本次工具输出的真实receipt路径：

```sh
python3 tools/tvkit.py --serial "$TV_ENDPOINT" restore-home --receipt state/home-TRANSACTION.json
python3 tools/tvkit.py --serial "$TV_ENDPOINT" restore-home --receipt state/home-TRANSACTION.json --apply
```

restore生成新事务，不覆盖旧记录；设备绑定不一致、原桌面不可用或API不符就停。恢复默认解析不等于已验证按Home键、焦点和重启效果，这些需要实机操作。

如果还没用过本工具，没有相应receipt，可以在系统默认应用设置里选择原桌面，或以体检时记录的真实HOME作为目标，用home命令预览后执行。历史原设备有LTvLauncher，但其他用户不能假定同一个第三方桌面已经安装。

## APK回装

查看 `state/backup-*/manifest.json`，核对状态、包名和每件文件摘要。单APK正常 `install --user 0 -r`，split按同一包完整集合 `install-multiple --user 0 -r`。只使用自己备份的同签名、系统允许的版本。Android拒绝降级时停止，不以卸载清数据“恢复”。

新增普通应用可在系统设置里卸载。直接ADB卸载不是所有者策略回退；实验DPC应先完成正常撤销并确认无owner/admin，保留需要的恢复材料后再卸载。

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
