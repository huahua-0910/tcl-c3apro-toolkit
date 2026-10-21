# 适配与验证矩阵

初始记录日期：2026-10-21。记录来自一台用户设备，不代表同系列所有固件。未附原始私有日志，下面是按实际证据范围整理的匿名摘要。

## 设备边界

| 项目 | 历史观察 |
| --- | --- |
| 产品 | TCL 27C3A Pro；Android model 返回 C3APRO |
| 系统 | Android 14 / API 34 |
| 原生 ABI | armeabi-v7a，即32位 ARM；不能仅凭SoC是64位就选ARM64 APK |
| 内存 | 约1.78 GiB可见RAM；后台服务宜按需运行 |
| 显示 | 物理3840×2160/60Hz；历史正常逻辑界面1920×1080、density320 |
| 视频路径 | Realtek硬解与厂商SIDEband，普通抓屏可能抓不到视频像素 |
| 权限 | 普通ADB不是root；hidden、enabled、installed是不同状态 |

此逻辑分辨率和density不是所有固件的通用推荐值。先保存本机原值。

## 结果分层

`PASS_HISTORICAL`：原单机历史实测；`PARTIAL`：只完成部分链路；`LOCAL_CHECK`：公开代码的本地检查；`NOT_RUN`：当前未执行。发布时的精确工具检查见 [版本记录](../CHANGELOG.md)。

| 项目 | 级别 | 说明 |
| --- | --- | --- |
| Google恢复 | PASS_HISTORICAL | 固定两批15项解除隐藏；后续相关已装包状态读回正常。管理身份已撤销。 |
| 官方Google Home/Play | PASS_HISTORICAL | 正常初始化后在线主页、方向键、Play目录与账号入口正常；历史主页回退往返通过。 |
| 官方YouTube | PARTIAL | 旧版画面/声音经人工确认；更新版时钟与硬解检查通过，未完整复验持续4K60。 |
| 4K60流畅度 | PARTIAL | 历史安静区间仍约0.7%–1%掉帧，不能写成已修复。 |
| HDR/杜比 | PARTIAL | 公共API声明DV/HDR10/HLG；原厂4K Profile5样片基础画面正常。非全Profile/认证验收。 |
| 缩放修复 | PASS_HISTORICAL | 本机持久density修复后实际重启保持；其他固件需独立判断。 |
| 设置入口旧版 | PASS_HISTORICAL | 四项按钮曾在本机实际打开；公开版换包名与签名后未在设备安装。 |
| newBV | PARTIAL | 来源/ABI/入口检查及启动；扫码登录和真实播放未验收。 |
| AirPlay Server | PARTIAL | Mac发现、电视PIN挑战；Mac/iPhone完整镜像与声音未验收。 |
| Google Cast/语音 | PARTIAL | 广播/服务基础发现；实投、手机遥控、实体麦克风未验收。 |
| 公开Python工具 | LOCAL_CHECK | 假ADB回归验证事务与失败路径；不是设备部署验收。 |
| 公开Android应用 | LOCAL_CHECK | 两个APK可编译且验签；公开包名未作设备执行。 |

测试另一固件时补充日期、型号/API/ABI、上游版本、动作、结果与首个失败。固件版本需人工去掉设备唯一标识；保留厂商公开版本号即可。
