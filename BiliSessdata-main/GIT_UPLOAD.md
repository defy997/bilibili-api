# 上传项目到GitHub - 详细步骤

## 前提条件

1. 已安装 Git
2. 已有 GitHub 账号
3. 已在本地登录获取了 token（运行过 `login.py`）

## 步骤1: 在GitHub上创建新仓库

1. 登录 GitHub
2. 点击右上角的 `+` 号，选择 `New repository`
3. 填写仓库信息：
   - **Repository name**: 例如 `BiliSessdata` 或 `BiliSessDataShare`
   - **Description**: 可选，例如 "B站SESSDATA自动刷新"
   - **Visibility**: 选择 `Public`（公开）或 `Private`（私有）
   - **不要**勾选 "Initialize this repository with a README"（如果已有代码）
4. 点击 `Create repository`

## 步骤2: 初始化本地Git仓库（如果还没有）

打开终端/命令行，进入项目目录：

```bash
cd D:\code\model\BiliSessdata-main\BiliSessdata-main
```

如果还没有初始化git，运行：

```bash
git init
```

## 步骤3: 检查要提交的文件

确保敏感文件不会被提交（已配置在 `.gitignore` 中）：
- ✅ `tokens.json` - 已忽略
- ✅ `bilibili_qrcode.png` - 已忽略
- ✅ `__pycache__/` - 已忽略

## 步骤4: 添加文件到Git

```bash
# 添加所有文件（.gitignore会自动排除敏感文件）
git add .

# 查看将要提交的文件（确认没有敏感文件）
git status
```

## 步骤5: 提交代码

```bash
git commit -m "Initial commit: B站SESSDATA自动刷新项目"
```

## 步骤6: 连接到GitHub远程仓库

将 `YOUR_USERNAME` 和 `YOUR_REPO_NAME` 替换为你的GitHub用户名和仓库名：

```bash
# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 例如：
# git remote add origin https://github.com/yourname/BiliSessdata.git
```

## 步骤7: 推送代码到GitHub

```bash
# 推送到main分支
git branch -M main
git push -u origin main
```

如果遇到认证问题，可能需要：
- 使用 Personal Access Token 作为密码
- 或配置 SSH 密钥

## 步骤8: 验证上传

1. 访问你的GitHub仓库页面
2. 确认所有文件都已上传
3. 确认 `tokens.json` 和二维码图片**没有**被上传

## 常见问题

### 问题1: 需要输入用户名和密码

**解决方案**: 使用 Personal Access Token
1. 访问 https://github.com/settings/tokens
2. 生成新 token（classic）
3. 勾选 `repo` 权限
4. 复制 token
5. 推送时，用户名输入你的GitHub用户名，密码输入token

### 问题2: 已经存在远程仓库

如果之前已经添加过远程仓库，先删除再添加：

```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

### 问题3: 推送被拒绝

如果远程仓库已有内容，需要先拉取：

```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

## 后续操作

上传成功后，你可以：

1. **设置自动刷新**（本地方式）：
   - 使用 Windows 任务计划程序每天运行 `refresh_local.py`
   - 或使用 GitHub Actions（需要配置Secrets）

2. **访问SESSDATA**：
   - 通过 `https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO_NAME/main/SESSDATA` 访问

3. **更新代码**：
   ```bash
   git add .
   git commit -m "更新说明"
   git push
   ```

