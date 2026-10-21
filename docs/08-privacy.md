# 公开化与隐私

公开仓库采用重新编排、显式选入的材料，不迁移原始施工目录或Git历史。它保留解释与可复用代码，把个人设备状态留在本人电脑。

## 公开内容

型号/API/ABI、非唯一能力参数、匿名结果摘要、正常Android操作方法、自己编写的工具与设置入口、第一方来源链接。第三方软件仅链接其发布页面，不重打包；厂商说明书和媒体样片不随仓库分发。

## 本地保留内容

账号/邮箱、IP和MAC、设备ID/序列号、配对码、SSID、代理订阅/节点/令牌、Cookie、截图/录像、应用数据库、签名密钥、原APK和split备份、原始logcat/bugreport/dumpsys以及原电脑绝对路径。`state/`、`build/`、`dist/`被Git忽略。

## 提交前

1. 先人工看差异和每个新增文件；若是界面图，遮挡账号/二维码/设备标识并移除元数据。项目初版没有截图。
2. `git add`明确选入文件后运行 `python3 tools/audit_public.py`：Git模式读取实际暂存blob，避免工作区已清理、暂存区却还保留旧秘密。另跑 `python3 tools/audit_public.py --source tree` 检查当前源文件树，包括未暂存文本；默认排除本地state/build/dist和.git等目录。
3. 发布前再跑 `python3 tools/audit_public.py --history`，检查暂存区及所有可达引用中的历史文件blob；CI会获取完整历史并运行这项检查。历史模式不审计commit作者元数据、远端已删除引用、issue、Release附件或外部缓存；这些仍需单独检查。
4. `git diff --cached --check`检查空白。扫描只报告文件名与规则，不回显疑似秘密原文。ZIP解压没有Git元数据时自动使用tree模式；ZIP不能检查Git历史。
5. 确认Git暂存列表只有计划公开的文本。APK仅经审核后放Release，不跟踪在Git历史。
6. issue只填型号/API/ABI、去标识的公开固件版本、包名与相关错误摘要；不贴完整原始日志。

自动扫描覆盖常见路径、IPv4/IPv6地址、MAC、令牌/私钥、Cookie/Authorization头、敏感赋值与URI；回环与标准文档示例网段允许出现。但仍可能漏掉混淆、截图、未知格式或低熵秘密，不能宣称绝对无敏感信息。

若发现已公开凭据，先撤销对应凭据并联系仓库维护者处理历史；删掉当前文件不能消除既有Git副本。报告时使用GitHub私密安全报告（若已启用）或脱敏issue，不在公开issue展示实际秘密。
