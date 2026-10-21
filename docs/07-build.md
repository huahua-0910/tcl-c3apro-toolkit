# 构建本项目Android工具

需要JDK17、Android SDK Platform34、Build Tools35.0.0，以及Python3.10+。通过Google官方SDK Manager准备工具，不从本仓库下载SDK/JDK。脚本不下载依赖、不连接ADB、不安装APK。

在本地设置以下路径：`JAVA_HOME` 为JDK17；`ANDROID_HOME` 为SDK根目录。

```sh
python3 tools/build_android.py --app settings-hub \
  --java-home "$JAVA_HOME" \
  --sdk-jar "$ANDROID_HOME/platforms/android-34/android.jar" \
  --build-tools "$ANDROID_HOME/build-tools/35.0.0"
```

进阶DPC只将app参数换为 `google-policy`。所有源码为Java与原生XML，无第三方Android库或原生ABI库；设置入口minSdk23，DPC仅支持API34/model C3APRO。

输出在 `dist/`：APK、签名验证文本、包含各源码摘要的构建回执。回执不含本地绝对路径。签名材料首次在 `state/signing/应用名/` 生成，权限受限；只用于本地构建，绝不提交。自行构建会使用自己的证书，不能覆盖不同证书签名的旧公开APK；不要通过卸载来假装无损升级。

设置入口包名 `io.github.huahua0910.c3apro.settings`；实验DPC为 `io.github.huahua0910.c3apro.policy`。它们与历史私人包名不同。旧版同逻辑的实机通过不等于新包名通过；公开版两包仅作编译/验签，设备执行标记NOT_RUN。

首版Release只分发无权限设置入口及其校验材料。实验DPC需要阅读管理权限分支后自行编译，避免把整机管理实验混进普通安装包。

本地开发验证：

```sh
python3 -m unittest discover -s tests -v
python3 tools/audit_public.py
git diff --check
```

隐私检查针对Git跟踪文件；新增文件先 `git add` 再扫描。脚本不能代替人工审阅，也不扫描本地忽略的私人目录。发布APK前另做manifest权限、DEX字符串、原生库与签名检查。项目未声称APK字节可重现构建：签名、时间和工具链会影响字节；源码摘要用于追溯。
