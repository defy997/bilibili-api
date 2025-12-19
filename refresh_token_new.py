"""
尝试使用新的refresh_token API端点
根据搜索结果，B站可能使用不同的刷新端点
"""
import json
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

def test_new_refresh_api():
    # 读取token
    with open('tokens.json', 'r', encoding='utf-8') as f:
        tokens = json.load(f)
    
    sessdata = tokens.get('sessdata')
    refresh_token = tokens.get('refresh_token')
    
    print("=" * 60)
    print("测试新的refresh_token API端点")
    print("=" * 60)
    print(f"SESSDATA: {sessdata}")
    print(f"Refresh Token: {refresh_token[:20]}...")
    print()
    
    # 方法1: 使用新的端点 /x/passport-login/web/confirm/refresh
    # 需要 csrf token (bili_jct)，但我们没有，先尝试不带csrf
    print("方法1: 尝试 /x/passport-login/web/confirm/refresh (需要csrf)...")
    try:
        url = "https://passport.bilibili.com/x/passport-login/web/confirm/refresh"
        cookies = {
            'SESSDATA': sessdata
        }
        data = {
            'refresh_token': refresh_token
            # 注意：可能需要 csrf，但我们先尝试不带
        }
        
        r = requests.post(url, data=data, cookies=cookies, headers=BILIBILI_HEADERS, timeout=10)
        print(f"状态码: {r.status_code}")
        result = r.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('code') == 0:
            print("✅ 方法1成功!")
            return True
        else:
            print(f"❌ 方法1失败: {result.get('message')}")
    except Exception as e:
        print(f"❌ 方法1异常: {e}")
    
    print()
    
    # 方法2: 尝试使用 access_key 参数（因为access_token测试时用的是access_key）
    print("方法2: 尝试使用 access_key 参数...")
    try:
        url = "https://passport.bilibili.com/api/v2/oauth2/refresh_token"
        params = {
            'access_key': tokens.get('access_token'),  # 使用 access_key
            'appkey': APPKEY,
            'refresh_token': refresh_token
        }
        
        # 计算签名
        items = sorted(params.items())
        sign_str = f"{urlencode(items)}{APPSEC}"
        sign = md5(sign_str.encode('utf-8')).hexdigest()
        params['sign'] = sign
        
        r = requests.post(url, params=params, headers=BILIBILI_HEADERS, timeout=10)
        print(f"状态码: {r.status_code}")
        result = r.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('code') == 0:
            print("✅ 方法2成功!")
            return True
        else:
            print(f"❌ 方法2失败: {result.get('message')}")
    except Exception as e:
        print(f"❌ 方法2异常: {e}")
    
    print()
    print("=" * 60)
    print("所有方法都失败了，可能需要:")
    print("1. 获取 bili_jct (CSRF token)")
    print("2. 使用不同的API端点")
    print("3. 或者定期重新登录")
    
    return False

if __name__ == "__main__":
    test_new_refresh_api()

