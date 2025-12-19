"""
帮助脚本：将token上传到GitHub Secrets
需要先安装: pip install requests pynacl
"""
import json
import os
import sys
from base64 import b64encode
from nacl import encoding, public
import requests


def encrypt(public_key: str, secret_value: str) -> str:
    """使用GitHub公钥加密值"""
    public_key_obj = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key_obj)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def get_public_key(token: str, owner: str, repo: str):
    """获取GitHub仓库的公钥"""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"获取公钥失败: {response.status_code} - {response.text}")
    return response.json()['key_id'], response.json()['key']


def update_secret(token: str, owner: str, repo: str, secret_name: str, secret_value: str, key_id: str, public_key: str):
    """更新GitHub Secret"""
    encrypted_value = encrypt(public_key, secret_value)
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}'
    }
    data = {
        'encrypted_value': encrypted_value,
        'key_id': key_id
    }
    response = requests.put(url, headers=headers, json=data)
    return response.status_code


def main():
    print("=" * 60)
    print("GitHub Secrets 配置助手")
    print("=" * 60)
    
    # 检查tokens.json文件
    if not os.path.exists('tokens.json'):
        print("❌ 错误: 未找到 tokens.json 文件")
        print("请先运行 login.py 进行登录")
        sys.exit(1)
    
    # 读取token信息
    with open('tokens.json', 'r', encoding='utf-8') as f:
        tokens = json.load(f)
    
    print(f"\n从 tokens.json 读取到以下信息:")
    print(f"  - Access Token: {tokens['access_token'][:20]}...")
    print(f"  - Refresh Token: {tokens['refresh_token'][:20]}...")
    print(f"  - SESSDATA: {tokens['sessdata']}")
    
    # 获取GitHub信息
    print("\n" + "=" * 60)
    print("请输入GitHub仓库信息:")
    owner = input("GitHub用户名/组织名: ").strip()
    repo = input("仓库名: ").strip()
    
    print("\n需要GitHub Personal Access Token (PAT)")
    print("创建步骤:")
    print("1. 访问 https://github.com/settings/tokens")
    print("2. 点击 'Generate new token (classic)'")
    print("3. 勾选权限: repo (全部), workflow")
    print("4. 生成并复制token")
    print()
    
    github_token = input("GitHub Personal Access Token: ").strip()
    
    if not github_token or not owner or not repo:
        print("❌ 错误: 信息不完整")
        sys.exit(1)
    
    try:
        print("\n正在获取GitHub公钥...")
        key_id, public_key = get_public_key(github_token, owner, repo)
        print(f"✅ 获取公钥成功 (key_id: {key_id})")
        
        # 更新ACCESS_TOKEN
        print("\n正在更新 ACCESS_TOKEN...")
        status = update_secret(github_token, owner, repo, 'ACCESS_TOKEN', 
                              tokens['access_token'], key_id, public_key)
        if status == 201 or status == 204:
            print("✅ ACCESS_TOKEN 更新成功")
        else:
            print(f"❌ ACCESS_TOKEN 更新失败: HTTP {status}")
        
        # 更新REFRESH_TOKEN
        print("\n正在更新 REFRESH_TOKEN...")
        status = update_secret(github_token, owner, repo, 'REFRESH_TOKEN', 
                              tokens['refresh_token'], key_id, public_key)
        if status == 201 or status == 204:
            print("✅ REFRESH_TOKEN 更新成功")
        else:
            print(f"❌ REFRESH_TOKEN 更新失败: HTTP {status}")
        
        # 更新REPO_ACCESS_TOKEN（用于GitHub Actions提交代码）
        print("\nREPO_ACCESS_TOKEN 用于GitHub Actions自动提交代码")
        use_same_token = input("是否使用同一个token作为REPO_ACCESS_TOKEN? (y/n): ").strip().lower()
        if use_same_token == 'y':
            print("\n正在更新 REPO_ACCESS_TOKEN...")
            status = update_secret(github_token, owner, repo, 'REPO_ACCESS_TOKEN', 
                                  github_token, key_id, public_key)
            if status == 201 or status == 204:
                print("✅ REPO_ACCESS_TOKEN 更新成功")
            else:
                print(f"❌ REPO_ACCESS_TOKEN 更新失败: HTTP {status}")
        else:
            print("⚠️  请手动在GitHub仓库设置中添加 REPO_ACCESS_TOKEN")
            print("   路径: Settings -> Secrets and variables -> Actions")
        
        print("\n" + "=" * 60)
        print("✅ 配置完成!")
        print("=" * 60)
        print("\n下一步:")
        print("1. 确保 .github/workflows/refresh.yml 文件已创建")
        print("2. 将代码推送到GitHub")
        print("3. GitHub Actions会自动在每天00:00(北京时间)刷新SESSDATA")
        print("4. 也可以手动在Actions页面触发工作流")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

