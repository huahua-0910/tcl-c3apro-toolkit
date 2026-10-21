# 应用选择与安装

这是2026-10-21来源与历史安装摘要，不是永远的“最新版”列表。第三方APK从第一方Release取得，安装前核对实际ABI、签名、split依赖与电视入口。32位系统不接受仅有ARM64原生库的APK。

| 应用 | 来源与建议 | 本机历史验收范围 |
| --- | --- | --- |
| YouTube大屏版 | 优先恢复本机 `com.google.android.youtube.tv`，再从Play更新。别与美国付费直播YouTube TV产品混淆。 | 旧版画面声音；更新版时钟与硬解，持续4K仍待复验。 |
| Google Play/Home | 优先本机原厂预装、正常初始化、Play更新。 | 单机基础可用和回退往返。 |
| FlClash | [作者仓库](https://github.com/chen08209/FlClash)，选真实armeabi-v7a包。本人合法配置在设备本地导入。 | 历史0.9.1保留原配置；没有附任何节点/订阅。 |
| 夸克TV | [官网](https://pan.quark.cn/)及[官网版本接口](https://pan.quark.cn/api/client_version)。历史官网为2.9.1702/CP。 | 同签名、同版本从TCL渠道覆盖到CP，原账号与媒体库保留；不是版本升级。 |
| 哔哩哔哩TV | [官方应用入口](https://app.bilibili.com/)，原云视听小电视保留。 | 原应用未替换。 |
| newBV | [作者发行页](https://github.com/Frost819/newBV/releases)。第三方客户端，不是官方海外TV版。 | 历史1.1.0来源、ARM32、入口；真实登录播放未验收。作者声明不支持中国大陆地区内使用，不承诺当地可用。 |
| AirPlay Server | [作者仓库](https://github.com/jqssun/android-airplay-server)、[0.0.36](https://github.com/jqssun/android-airplay-server/releases/tag/v0.0.36)。按需打开。 | 仅发现和PIN阶段；完整投屏/声音未验收。 |
| Kodi | [官方下载](https://kodi.tv/download/android/)，本地/NAS媒体可选。 | 本轮未安装；云盘方案不是已部署内容。 |

## 普通APK更新

先备份目标包的全部APK。使用Android Build Tools的apksigner检查文件签名；覆盖已装应用应比较签名证书，版本降级或签名不一致就停。需要base+split时整组使用install-multiple，不能只装base。

```sh
apksigner verify --verbose --print-certs ./app.apk
adb -s "$TV_ENDPOINT" install --user 0 -r ./app.apk
```

这条命令是手动示例，不会自动下载安装任何应用。普通覆盖也不能承诺所有应用私有数据与服务端状态完全可逆；不要通过卸载/清数据绕过签名不一致。安装后独立确认实际包名/版本、用户0状态、真实入口、遥控器和原有账号。

## Mac / iPhone投屏

电视打开AirPlay Server，发送端与电视在可相互发现的局域网；Mac/iPhone使用系统“屏幕镜像”。保留PIN验证，按设备页面完成配对。

历史初始配置为按需启动、无开机自启、退出不保持后台，1080p30请求上限、ALAC开启。请求上限不等于最终协商实测值。DRM视频和4K/HDR不是普通AirPlay镜像必然支持的能力；实际声音、清晰度和稳定性要单独验收。

## 暂不部署的路线

CleanYourTV未部署：它的批量应用名单与桌面操作不能直接套本机。本项目不继承其卸载清单。

夸克海报墙可以用OpenList桥接WebDAV后接Kodi，但夸克驱动属逆向且不主动维护，Mac/NAS需要在线。本次使用场景不接受Mac常驻，因此不纳入部署步骤。[驱动说明](https://doc.oplist.org/guide/drivers/quark)

William Player当前已检查的1.5.0公开APK只有ARM64；README写有TV/ARM32不能代替真实包检查。OmniPlay是WebDAV前端，仍需要桥接，均未在本机安装。不把项目的研究候选当成功能交付。
