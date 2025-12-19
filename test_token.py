"""
测试B站token是否有效的脚本
"""
import json
import time
import requests
from urllib.parse import urlencode
from hashlib import md5

APPKEY = "4409e2ce8ffd12b8"
APPSEC = "59b43e04ad6965f34319062b478f83dd"

BILIBILI_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
    'Origin': 'https://www.bilibili.com',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Content-Type': 'application/x-www-form-urlencoded',
}

def get_sign(params):
    items = sorted(params.items())
    return md5(f"{urlencode(items)}{APPSEC}".encode('utf-8')).hexdigest()

def test_token():
    # 读取token
    with open('tokens.json', 'r', encoding='utf-8') as f:
        tokens = json.load(f)
    
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')
    
    print("=" * 60)
    print("测试B站Token有效性")
    print("=" * 60)
    print(f"Access Token: {access_token[:20]}...")
    print(f"Refresh Token: {refresh_token[:20]}...")
    print()
    
    # 测试1: 尝试使用access_token获取用户信息（B站可能使用access_key参数）
    print("测试1: 使用access_token获取用户信息...")
    try:
        # 方式1: 使用access_key参数
        url = "https://api.bilibili.com/x/space/myinfo"
        params = {
            'access_key': access_token,
            'appkey': APPKEY,
            'ts': int(time.time())
        }
        params['sign'] = get_sign(params)
        
        r = requests.get(url, params=params, headers=BILIBILI_HEADERS, timeout=10)
        print(f"状态码: {r.status_code}")
        result = r.json()
        print(f"响应: {result}")
        if result.get('code') == 0:
            print("✅ access_token 有效")
        else:
            print(f"❌ access_token 无效: {result.get('message')}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print()
    
    # 测试2: 尝试刷新token
    print("测试2: 尝试刷新token...")
    # 尝试使用 access_key 而不是 access_token
    params1 = {
        'access_key': access_token,  # 尝试使用 access_key
        'appkey': APPKEY,
        'refresh_token': refresh_token
    }
    params1['sign'] = get_sign(params1)
    
    print(f"尝试1 - 使用 access_key:")
    print(f"请求参数: {list(params1.keys())}")
    print(f"签名: {params1['sign']}")
    
    try:
        url = "https://passport.bilibili.com/api/v2/oauth2/refresh_token"
        r = requests.post(url, params=params1, headers=BILIBILI_HEADERS, timeout=10)
        print(f"状态码: {r.status_code}")
        result = r.json()
        print(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('code') == 0:
            print("✅ refresh_token 有效（使用 access_key）")
            return
        else:
            print(f"❌ 使用 access_key 失败: {result.get('message')}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print()
    print("尝试2 - 使用 access_token:")
    params2 = {
        'access_token': access_token,  # 使用 access_token
        'appkey': APPKEY,
        'refresh_token': refresh_token
    }
    params2['sign'] = get_sign(params2)
    print(f"请求参数: {list(params2.keys())}")
    print(f"签名: {params2['sign']}")
    
    try:
        r = requests.post(url, params=params2, headers=BILIBILI_HEADERS, timeout=10)
        print(f"状态码: {r.status_code}")
        result = r.json()
        print(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('code') == 0:
            print("✅ refresh_token 有效，可以刷新")
        else:
            print(f"❌ refresh_token 刷新失败:")
            print(f"   错误码: {result.get('code')}")
            print(f"   错误信息: {result.get('message')}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print()
    print("=" * 60)
    print("如果两个测试都失败，说明token已过期，需要重新登录")
    print("运行: python login.py")

if __name__ == "__main__":
    test_token()

