"""
本地刷新SESSDATA脚本
从tokens.json读取token，刷新后更新tokens.json和SESSDATA文件
"""
import json
import os
from datetime import datetime
from hashlib import md5
from urllib.parse import urlencode

import requests
import pytz

APPKEY = "4409e2ce8ffd12b8"
APPSEC = "59b43e04ad6965f34319062b478f83dd"


def get_sign(params):
    items = sorted(params.items())
    return md5(f"{urlencode(items)}{APPSEC}".encode('utf-8')).hexdigest()


def refresh_local():
    """从本地tokens.json读取token并刷新"""
    # 检查tokens.json文件
    tokens_file = "tokens.json"
    if not os.path.exists(tokens_file):
        print(f"❌ 错误: 未找到 {tokens_file} 文件")
        print("请先运行 login.py 进行登录")
        return False
    
    # 读取token信息
    with open(tokens_file, 'r', encoding='utf-8') as f:
        tokens = json.load(f)
    
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')
    
    if not access_token or not refresh_token:
        print("❌ 错误: tokens.json 中缺少 access_token 或 refresh_token")
        return False
    
    print("正在刷新SESSDATA...")
    
    # 调用刷新接口
    params = {
        'access_token': access_token,
        'appkey': APPKEY,
        'refresh_token': refresh_token
    }
    params['sign'] = get_sign(params)
    url = "https://passport.bilibili.com/api/v2/oauth2/refresh_token"
    
    try:
        response = requests.post(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') != 0:
            print(f"❌ 刷新失败: {data.get('message', '未知错误')}")
            return False
        
        result_data = data['data']
        new_access_token = result_data['token_info']['access_token']
        new_refresh_token = result_data['token_info']['refresh_token']
        
        # 从cookies中查找SESSDATA
        sessdata = None
        for cookie in result_data['cookie_info']['cookies']:
            if cookie.get('name') == 'SESSDATA':
                sessdata = cookie.get('value')
                break
        
        if not sessdata:
            print("❌ 错误: 未找到SESSDATA")
            return False
        
        # 更新tokens.json
        tokens['access_token'] = new_access_token
        tokens['refresh_token'] = new_refresh_token
        tokens['sessdata'] = sessdata
        tokens['last_refreshed'] = datetime.now().isoformat()
        
        with open(tokens_file, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)
        
        # 更新SESSDATA文件
        sessdata_info = {
            'value': sessdata,
            'updated': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S %Z')
        }
        
        with open('SESSDATA', 'w', encoding='utf-8') as f:
            f.write(json.dumps(sessdata_info, ensure_ascii=False))
        
        print("✅ SESSDATA刷新成功!")
        print(f"   SESSDATA: {sessdata}")
        print(f"   更新时间: {sessdata_info['updated']}")
        print(f"   Token已更新到 {tokens_file}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    refresh_local()

