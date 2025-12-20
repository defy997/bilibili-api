import json
import os
import time
import re
from base64 import b64encode
from datetime import datetime
from hashlib import md5
from urllib.parse import urlencode

import requests
import pytz
from nacl import encoding, public
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
import binascii


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

REFRESH_TOKEN = os.environ['REFRESH_TOKEN']
SESSDATA = os.environ.get('SESSDATA')
BILI_JCT = os.environ.get('BILI_JCT')
MID = os.environ.get('MID')

# B站公钥（用于生成CorrespondPath）
BILIBILI_PUBLIC_KEY = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDLgd2OAkcGVtoE3ThUREbio0Eg
Uc/prcajMKXvkCKFCWhJYJcLkcM2DKKcSeFpD/j6Boy538YXnR6VhcuUJOhH2x71
nzPjfdTcqMz7djHum0qSZA0AyCBDABUqCrfNgCiJ00Ra7GmRj+YCK1NJEuewlb40
JNrRuoEUXpabUzGB8QIDAQAB
-----END PUBLIC KEY-----'''

# 添加必要的请求头，避免被B站安全策略拦截
BILIBILI_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
    'Origin': 'https://www.bilibili.com',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def get_correspond_path(timestamp):
    """生成CorrespondPath签名（RSA-OAEP加密）"""
    key = RSA.importKey(BILIBILI_PUBLIC_KEY)
    cipher = PKCS1_OAEP.new(key, SHA256)
    encrypted = cipher.encrypt(f'refresh_{timestamp}'.encode())
    return binascii.b2a_hex(encrypted).decode()


def check_need_refresh(cookies):
    """检查是否需要刷新Cookie"""
    url = "https://passport.bilibili.com/x/passport-login/web/cookie/info"
    try:
        response = requests.get(url, cookies=cookies, headers=BILIBILI_HEADERS, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            data = result.get('data', {})
            return data.get('refresh', False), data.get('timestamp')
        return False, None
    except Exception as e:
        print(f"检查刷新状态失败: {e}")
        return False, None


def get_refresh_csrf(correspond_path, cookies):
    """获取refresh_csrf实时刷新口令"""
    url = f"https://www.bilibili.com/correspond/1/{correspond_path}"
    try:
        response = requests.get(url, cookies=cookies, headers=BILIBILI_HEADERS, timeout=10)
        response.raise_for_status()
        
        # 从HTML中提取refresh_csrf
        html = response.text
        match = re.search(r'<div id="1-name">([^<]+)</div>', html)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        print(f"获取refresh_csrf失败: {e}")
        return None


def refresh_cookie(refresh_token, refresh_csrf, cookies):
    """刷新Cookie获取新会话"""
    url = "https://passport.bilibili.com/x/passport-login/web/cookie/refresh"
    data = {
        'csrf': cookies.get('bili_jct', ''),
        'refresh_csrf': refresh_csrf,
        'source': 'main_web',
        'refresh_token': refresh_token
    }
    
    try:
        response = requests.post(url, data=data, cookies=cookies, headers=BILIBILI_HEADERS, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            # 获取新的Cookie（从响应头）
            new_cookies = {}
            for cookie in response.cookies:
                new_cookies[cookie.name] = cookie.value
            
            # 合并新旧Cookie
            updated_cookies = {**cookies, **new_cookies}
            
            # 获取新的refresh_token
            new_refresh_token = result.get('data', {}).get('refresh_token')
            
            return updated_cookies, new_refresh_token
        else:
            print(f"刷新失败: {result.get('message')}")
            return None, None
    except Exception as e:
        print(f"刷新Cookie失败: {e}")
        return None, None


def confirm_refresh(old_refresh_token, cookies):
    """确认更新使旧会话失效"""
    url = "https://passport.bilibili.com/x/passport-login/web/confirm/refresh"
    data = {
        'csrf': cookies.get('bili_jct', ''),
        'refresh_token': old_refresh_token
    }
    
    try:
        response = requests.post(url, data=data, cookies=cookies, headers=BILIBILI_HEADERS, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get('code') == 0
    except Exception as e:
        print(f"确认更新失败: {e}")
        return False

def refresh():
    """使用B站官方Cookie刷新机制"""
    print("=" * 60)
    print("B站Cookie刷新流程（官方方法）")
    print("=" * 60)
    
    if not SESSDATA or not BILI_JCT or not REFRESH_TOKEN:
        raise ValueError("缺少必要的环境变量: SESSDATA, BILI_JCT, REFRESH_TOKEN")
    
    # 构建Cookie
    cookies = {
        'SESSDATA': SESSDATA,
        'bili_jct': BILI_JCT,
    }
    if MID:
        cookies['DedeUserID'] = str(MID)
    
    # 步骤1: 检查是否需要刷新
    print("\n步骤1: 检查是否需要刷新...")
    need_refresh, timestamp = check_need_refresh(cookies)
    
    if not need_refresh:
        print("✅ Cookie仍然有效，无需刷新")
        print("直接更新SESSDATA文件...")
        
        sessdata_info = {
            'value': SESSDATA,
            'updated': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S %Z')
        }
        
        with open('SESSDATA', 'w', encoding='utf-8') as f:
            f.write(json.dumps(sessdata_info, ensure_ascii=False))
        
        print("✅ SESSDATA文件已更新!")
        return None, REFRESH_TOKEN, SESSDATA
    
    print(f"⚠️  需要刷新Cookie (timestamp: {timestamp})")
    
    # 步骤2: 生成CorrespondPath
    print("\n步骤2: 生成CorrespondPath...")
    ts = timestamp or round(time.time() * 1000)
    correspond_path = get_correspond_path(ts)
    print(f"✅ CorrespondPath生成成功")
    
    # 步骤3: 获取refresh_csrf
    print("\n步骤3: 获取refresh_csrf...")
    refresh_csrf = get_refresh_csrf(correspond_path, cookies)
    if not refresh_csrf:
        raise Exception("获取refresh_csrf失败")
    print(f"✅ refresh_csrf获取成功")
    
    # 步骤4: 刷新Cookie
    print("\n步骤4: 刷新Cookie...")
    old_refresh_token = REFRESH_TOKEN
    new_cookies, new_refresh_token = refresh_cookie(REFRESH_TOKEN, refresh_csrf, cookies)
    
    if not new_cookies or not new_refresh_token:
        raise Exception("Cookie刷新失败")
    
    print("✅ Cookie刷新成功!")
    new_sessdata = new_cookies.get('SESSDATA', SESSDATA)
    new_bili_jct = new_cookies.get('bili_jct', BILI_JCT)
    
    # 步骤5: 确认更新
    print("\n步骤5: 确认更新（使旧会话失效）...")
    if confirm_refresh(old_refresh_token, new_cookies):
        print("✅ 确认更新成功")
    else:
        print("⚠️  确认更新失败，但Cookie已刷新")
    
    # 更新GitHub Secrets
    print("\n步骤6: 更新GitHub Secrets...")
    update_secret('REFRESH_TOKEN', new_refresh_token, KEY_ID, KEY)
    update_secret('SESSDATA', new_sessdata, KEY_ID, KEY)
    update_secret('BILI_JCT', new_bili_jct, KEY_ID, KEY)
    print("✅ GitHub Secrets更新成功")
    
    # 更新SESSDATA文件
    print("\n步骤7: 更新SESSDATA文件...")
    sessdata_info = {
        'value': new_sessdata,
        'updated': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S %Z')
    }
    
    with open('SESSDATA', 'w', encoding='utf-8') as f:
        f.write(json.dumps(sessdata_info, ensure_ascii=False))
    
    print(f"✅ SESSDATA刷新成功: {new_sessdata[:30]}...")
    print(f"   更新时间: {sessdata_info['updated']}")
    
    return None, new_refresh_token, new_sessdata


if __name__ == "__main__":
    try:
        print("正在获取GitHub公钥...")
        KEY_ID, KEY = get_public_key()
        print(f"✅ 获取公钥成功 (key_id: {KEY_ID})")
        
        # 刷新Cookie
        refresh()
        
        print("\n" + "=" * 60)
        print("✅ Cookie刷新流程完成!")
        print("=" * 60)
        
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
