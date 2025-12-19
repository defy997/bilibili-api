# 设置指南

## 步骤1: 登录获取Token

运行登录脚本：

```bash
python login.py
```

使用B站APP扫描二维码登录，登录成功后会在当前目录生成 `tokens.json` 文件。

## 步骤2: 配置GitHub Secrets

有两种方式配置GitHub Secrets：

### 方式1: 使用自动配置脚本（推荐）

```bash
python setup_github.py
```

脚本会引导你：
1. 输入GitHub用户名和仓库名
2. 输入GitHub Personal Access Token
3. 自动将 ACCESS_TOKEN 和 REFRESH_TOKEN 上传到GitHub Secrets

### 方式2: 手动配置

1. 打开你的GitHub仓库
2. 进入 `Settings` -> `Secrets and variables` -> `Actions`
3. 添加以下Secrets：
   - `ACCESS_TOKEN`: 从 `tokens.json` 中复制
   - `REFRESH_TOKEN`: 从 `tokens.json` 中复制
   - `REPO_ACCESS_TOKEN`: GitHub Personal Access Token（用于自动提交代码）

## 步骤3: 创建GitHub Personal Access Token

1. 访问 https://github.com/settings/tokens
2. 点击 `Generate new token (classic)`
3. 勾选以下权限：
   - `repo` (全部权限)
   - `workflow`
4. 生成并复制token

## 步骤4: 推送代码到GitHub

```bash
git add .
git commit -m "Initial commit"
git push
```

## 步骤5: 验证

1. 进入GitHub仓库的 `Actions` 页面
2. 应该能看到 `Refresh SESSDATA` 工作流
3. 可以手动触发一次测试
4. 工作流会在每天北京时间 00:00 自动运行

## 注意事项

- `tokens.json` 包含敏感信息，不要提交到GitHub
- 确保 `.gitignore` 包含 `tokens.json`
- SESSDATA 会自动更新到 `SESSDATA` 文件
- 可以通过以下链接访问最新的SESSDATA：
  - `https://raw.githubusercontent.com/你的用户名/仓库名/main/SESSDATA`

