import json
import os
from base64 import b64encode
from datetime import datetime
from hashlib import md5
from urllib.parse import urlencode

import requests
import pytz
from nacl import encoding, public


def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


token = os.environ['REPO_ACCESS_TOKEN']
# 从环境变量获取仓库信息，如果没有则使用默认值（需要手动修改）
owner = os.environ.get('GITHUB_OWNER', 'defy997')  # 改为你的GitHub用户名
repo = os.environ.get('GITHUB_REPO', 'bilibili-api')  # 改为你的仓库名
base_address = f"https://{owner}:{token}@api.github.com/repos/{owner}/{repo}/actions/secrets/"
headers={'accept': 'application/vnd.github.v3+json'}
proxies={'http': None, 'https': None}


def get(route):
    url = base_address + route
    try:
        response = requests.get(url, proxies=proxies, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP错误: {e}")
        print(f"响应内容: {response.text[:500] if hasattr(response, 'text') else 'N/A'}")
        raise
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        raise


def put(route, params):
    url = base_address + route
    data = json.dumps(params)
    try:
        response = requests.put(url, data=data, headers=headers, proxies=proxies, timeout=10)
        response.raise_for_status()
        return response.status_code
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP错误: {e}")
        print(f"响应内容: {response.text[:500] if hasattr(response, 'text') else 'N/A'}")
        raise
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        raise


def get_public_key():
    try:
        r = get('public-key')
        return r['key_id'], r['key']
    except KeyError as e:
        print(f"❌ 获取公钥失败，响应中缺少字段: {e}")
        raise
    except Exception as e:
        print(f"❌ 获取公钥失败: {e}")
        raise


def update_secret(name, value, key_id, public_key):
    encrypt_value = encrypt(public_key, value)
    params = {
        'encrypted_value': encrypt_value,
        'key_id': key_id
    }
    status = put(name, params)
    if status not in [201, 204]:
        print(f"⚠️  更新Secret {name} 返回状态码: {status}")
    return status

ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
REFRESH_TOKEN = os.environ['REFRESH_TOKEN']
APPKEY = "4409e2ce8ffd12b8"
APPSEC = "59b43e04ad6965f34319062b478f83dd"

def get_sign(params):
    items = sorted(params.items())
    return md5(f"{urlencode(items)}{APPSEC}".encode('utf-8')).hexdigest()

def refresh():
    params = {
        'access_token': ACCESS_TOKEN,
        'appkey': APPKEY,
        'refresh_token': REFRESH_TOKEN
    }
    params['sign'] = get_sign(params)
    url = f"https://passport.bilibili.com/api/v2/oauth2/refresh_token"
    
    try:
        response = requests.post(url, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # 检查API返回码
        if result.get('code') != 0:
            error_msg = result.get('message', '未知错误')
            print(f"❌ 刷新失败: {error_msg}")
            raise Exception(f"B站API返回错误: {error_msg}")
        
        r = result['data']
        access_token = r['token_info']['access_token']
        refresh_token = r['token_info']['refresh_token']
        
        # 从cookies中查找SESSDATA
        sessdata = None
        for cookie in r['cookie_info']['cookies']:
            if cookie.get('name') == 'SESSDATA':
                sessdata = cookie.get('value')
                break
        
        if not sessdata:
            raise ValueError("未找到SESSDATA")
        
        # 更新SESSDATA文件
        sessdata_info = {
            'value': sessdata,
            'updated': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S %Z')
        }
        
        with open('SESSDATA', 'w', encoding='utf-8') as f:
            f.write(json.dumps(sessdata_info, ensure_ascii=False))
        
        print(f"✅ SESSDATA刷新成功: {sessdata}")
        print(f"   更新时间: {sessdata_info['updated']}")
        
        # 返回新的token
        return access_token, refresh_token, sessdata
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求错误: {e}")
        raise
    except KeyError as e:
        print(f"❌ 响应数据格式错误，缺少字段: {e}")
        print(f"响应内容: {response.text if 'response' in locals() else 'N/A'}")
        raise
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        raise


if __name__ == "__main__":
    try:
        print("正在获取GitHub公钥...")
        KEY_ID, KEY = get_public_key()
        print(f"✅ 获取公钥成功 (key_id: {KEY_ID})")
        
        # 刷新token
        new_access_token, new_refresh_token, sessdata = refresh()
        
        # 更新GitHub Secrets
        print("正在更新GitHub Secrets...")
        update_secret('ACCESS_TOKEN', new_access_token, KEY_ID, KEY)
        update_secret('REFRESH_TOKEN', new_refresh_token, KEY_ID, KEY)
        print("✅ GitHub Secrets更新成功")
        
    except KeyError as e:
        print(f"❌ 环境变量或响应数据缺失: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
