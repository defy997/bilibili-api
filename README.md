# BiliSessdata

自动刷新并共享 B站 SESSDATA 的项目，使用 B站官方 Cookie 刷新机制，保证长期有效。

## ✨ 功能特性

- 🔐 **安全登录**：使用二维码扫码登录，安全便捷
- 🔄 **自动刷新**：基于 B站官方 Cookie 刷新机制，自动保持 SESSDATA 有效
- 🤖 **GitHub Actions**：每天自动刷新并更新到仓库
- 📦 **易于使用**：提供本地刷新脚本和 GitHub Actions 两种方式
- 🔒 **安全存储**：敏感信息加密存储在 GitHub Secrets

## 📋 什么是 SESSDATA？

SESSDATA 是 B站 的登录凭证，每个账户登录后都会在服务器生成一个单独的 SESSDATA。可以用 SESSDATA 来请求某些必须要登录状态才能访问的 API。

**注意**：SESSDATA 本身只具备**查看**权限，任何操作类 API（如点赞、投币、评论）都需要和 `bili_jct` 配合使用。本项目仅提供查看权限的 SESSDATA。

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/仓库名.git
cd 仓库名
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 登录获取 Token

运行登录脚本：

```bash
python login.py
```

使用 B站 APP 扫描二维码登录，登录成功后会在当前目录生成 `tokens.json` 文件。

### 4. 配置 GitHub Secrets

#### 方式1：使用自动配置脚本（推荐）

```bash
python setup_github.py
```

脚本会引导你：
1. 输入 GitHub 用户名和仓库名
2. 输入 GitHub Personal Access Token
3. 自动将必要的 Secrets 上传到 GitHub

#### 方式2：手动配置

1. 访问你的 GitHub 仓库
2. 进入 `Settings` -> `Secrets and variables` -> `Actions`
3. 添加以下 Secrets：
   - `REFRESH_TOKEN`: 从 `tokens.json` 中复制
   - `SESSDATA`: 从 `tokens.json` 中复制
   - `BILI_JCT`: 从 `tokens.json` 中复制
   - `MID`: 从 `tokens.json` 中复制（用户ID）
   - `REPO_ACCESS_TOKEN`: GitHub Personal Access Token（用于自动提交代码）

### 5. 创建 GitHub Personal Access Token

1. 访问 https://github.com/settings/tokens
2. 点击 `Generate new token (classic)`
3. 勾选权限：`repo`（全部权限）、`workflow`
4. 生成并复制 token

### 6. 推送代码到 GitHub

```bash
git add .
git commit -m "Initial commit"
git push
```

## 📖 使用方法

### 访问 SESSDATA

数据存储在根目录的 `SESSDATA` 文件，可以通过以下方式访问：

**GitHub Raw 链接**：
```
https://raw.githubusercontent.com/你的用户名/仓库名/main/SESSDATA
```

**返回格式**：
```json
{
  "value": "SESSDATA值",
  "updated": "2025-12-20 01:14:09 CST"
}
```

### 本地刷新

如果需要手动刷新，可以运行：

```bash
python refresh_local.py
```

脚本会：
1. 检查 Cookie 是否需要刷新
2. 如果需要，自动执行刷新流程
3. 更新 `tokens.json` 和 `SESSDATA` 文件

### GitHub Actions 自动刷新

配置完成后，GitHub Actions 会在每天北京时间 00:00 自动运行刷新流程。

你也可以在 GitHub 仓库的 `Actions` 页面手动触发工作流。

## 🔧 项目结构

```
.
├── login.py              # 二维码登录脚本
├── refresh_local.py      # 本地刷新脚本（使用官方Cookie刷新机制）
├── refresh.py            # GitHub Actions刷新脚本
├── setup_github.py      # GitHub Secrets配置助手
├── requirements.txt      # Python依赖
├── .github/
│   └── workflows/
│       └── refresh.yml   # GitHub Actions工作流配置
├── SESSDATA             # SESSDATA数据文件（自动更新）
├── tokens.json          # Token信息（本地存储，不提交）
└── README.md           # 项目说明文档
```

## 🔄 刷新机制说明

本项目使用 B站官方的 Cookie 刷新机制，流程如下：

1. **检查是否需要刷新**：调用 Cookie 信息接口判断当前会话是否需要刷新
2. **生成 CorrespondPath**：使用 RSA-OAEP 算法加密生成签名
3. **获取 refresh_csrf**：通过 CorrespondPath 获取实时刷新口令
4. **刷新 Cookie**：使用 refresh_csrf 和 refresh_token 刷新 Cookie
5. **确认更新**：使旧会话失效，确保账号安全

详细实现参考：[B站用户登录状态刷新接口开发](https://blog.csdn.net/gitblog_00169/article/details/152153957)

## ⚙️ 环境变量说明

### GitHub Secrets（用于 GitHub Actions）

- `REFRESH_TOKEN`: B站 refresh_token
- `SESSDATA`: B站 SESSDATA Cookie
- `BILI_JCT`: B站 bili_jct Cookie（CSRF Token）
- `MID`: B站用户ID
- `REPO_ACCESS_TOKEN`: GitHub Personal Access Token（用于提交代码）

## 📝 注意事项

- ⚠️ `tokens.json` 包含敏感信息，已加入 `.gitignore`，**不要提交到 GitHub**
- ⚠️ SESSDATA 会自动更新，旧值会直接失效，请做好异常处理
- ⚠️ 如果自动刷新失败，需要重新运行 `login.py` 登录
- ⚠️ 本项目仅供学习交流使用，请勿用于任何违法、商业用途

## 🛠️ 故障排除

### 刷新失败

如果刷新失败，可能的原因：
1. Token 已过期：运行 `python login.py` 重新登录
2. GitHub Secrets 未正确配置：运行 `python setup_github.py` 重新配置
3. 网络问题：检查网络连接

### 本地刷新失败

1. 确保已安装所有依赖：`pip install -r requirements.txt`
2. 确保 `tokens.json` 文件存在且包含必要信息
3. 检查网络连接

## 📚 相关文档

- [B站 API 文档](https://github.com/SocialSisterYi/bilibili-API-collect)
- [B站 Cookie 刷新文档](https://blog.csdn.net/gitblog_00169/article/details/152153957)

## 📄 许可证

本项目仅供学习交流使用。

## 🙏 致谢

- 基于 [BiliSessdata](https://github.com/SK-415/BiliSessdata) 项目
- Cookie 刷新机制参考 [哔哩哔哩-API收集整理](https://gitcode.com/GitHub_Trending/bi/bilibili-API-collect)
