"""
B站Cookie刷新实现
基于: https://blog.csdn.net/gitblog_00169/article/details/152153957
实现B站官方的Cookie刷新机制
"""
import json
import os
import time
import re
from datetime import datetime
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
import binascii
import requests
import pytz

BILIBILI_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
    'Origin': 'https://www.bilibili.com',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# B站公钥（用于生成CorrespondPath）
BILIBILI_PUBLIC_KEY = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDLgd2OAkcGVtoE3ThUREbio0Eg
Uc/prcajMKXvkCKFCWhJYJcLkcM2DKKcSeFpD/j6Boy538YXnR6VhcuUJOhH2x71
nzPjfdTcqMz7djHum0qSZA0AyCBDABUqCrfNgCiJ00Ra7GmRj+YCK1NJEuewlb40
JNrRuoEUXpabUzGB8QIDAQAB
-----END PUBLIC KEY-----'''


def get_correspond_path(timestamp):
    """生成CorrespondPath签名"""
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


def refresh_bilibili_cookie():
    """完整的Cookie刷新流程"""
    tokens_file = "tokens.json"
    if not os.path.exists(tokens_file):
        print(f"❌ 错误: 未找到 {tokens_file} 文件")
        print("请先运行 login.py 进行登录")
        return False
    
    # 读取token信息
    with open(tokens_file, 'r', encoding='utf-8') as f:
        tokens = json.load(f)
    
    sessdata = tokens.get('sessdata')
    bili_jct = tokens.get('bili_jct')
    refresh_token = tokens.get('refresh_token')
    mid = tokens.get('mid')
    
    if not sessdata or not bili_jct or not refresh_token:
        print("❌ 错误: tokens.json 中缺少必要信息")
        print("请运行 login.py 重新登录")
        return False
    
    # 构建Cookie
    cookies = {
        'SESSDATA': sessdata,
        'bili_jct': bili_jct,
    }
    if mid:
        cookies['DedeUserID'] = str(mid)
    
    print("=" * 60)
    print("B站Cookie刷新流程")
    print("=" * 60)
    
    # 步骤1: 检查是否需要刷新
    print("\n步骤1: 检查是否需要刷新...")
    need_refresh, timestamp = check_need_refresh(cookies)
    
    if not need_refresh:
        print("✅ Cookie仍然有效，无需刷新")
        print("直接更新SESSDATA文件...")
        
        sessdata_info = {
            'value': sessdata,
            'updated': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S %Z')
        }
        
        with open('SESSDATA', 'w', encoding='utf-8') as f:
            f.write(json.dumps(sessdata_info, ensure_ascii=False))
        
        print("✅ SESSDATA文件已更新!")
        return True
    
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
        print("❌ 获取refresh_csrf失败")
        return False
    print(f"✅ refresh_csrf获取成功: {refresh_csrf[:20]}...")
    
    # 步骤4: 刷新Cookie
    print("\n步骤4: 刷新Cookie...")
    old_refresh_token = refresh_token  # 保存旧的refresh_token
    new_cookies, new_refresh_token = refresh_cookie(refresh_token, refresh_csrf, cookies)
    
    if not new_cookies or not new_refresh_token:
        print("❌ Cookie刷新失败")
        return False
    
    print("✅ Cookie刷新成功!")
    print(f"   新的SESSDATA: {new_cookies.get('SESSDATA', 'N/A')[:30]}...")
    print(f"   新的refresh_token: {new_refresh_token[:20]}...")
    
    # 步骤5: 确认更新
    print("\n步骤5: 确认更新（使旧会话失效）...")
    if confirm_refresh(old_refresh_token, new_cookies):
        print("✅ 确认更新成功")
    else:
        print("⚠️  确认更新失败，但Cookie已刷新")
    
    # 更新tokens.json
    print("\n步骤6: 更新tokens.json...")
    tokens['sessdata'] = new_cookies.get('SESSDATA', sessdata)
    tokens['bili_jct'] = new_cookies.get('bili_jct', bili_jct)
    tokens['refresh_token'] = new_refresh_token
    tokens['last_refreshed'] = datetime.now().isoformat()
    
    with open(tokens_file, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    
    print("✅ tokens.json已更新")
    
    # 更新SESSDATA文件
    print("\n步骤7: 更新SESSDATA文件...")
    sessdata_info = {
        'value': new_cookies.get('SESSDATA', sessdata),
        'updated': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S %Z')
    }
    
    with open('SESSDATA', 'w', encoding='utf-8') as f:
        f.write(json.dumps(sessdata_info, ensure_ascii=False))
    
    print("✅ SESSDATA文件已更新!")
    print(f"   更新时间: {sessdata_info['updated']}")
    
    print("\n" + "=" * 60)
    print("✅ Cookie刷新流程完成!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        refresh_bilibili_cookie()
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

