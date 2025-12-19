"""
直接使用当前有效的token更新SESSDATA文件
当refresh_token API不工作时使用此脚本
"""
import json
import os
from datetime import datetime
import pytz

def update_sessdata():
    # 读取tokens.json
    tokens_file = "tokens.json"
    if not os.path.exists(tokens_file):
        print(f"❌ 错误: 未找到 {tokens_file} 文件")
        print("请先运行 login.py 进行登录")
        return False
    
    with open(tokens_file, 'r', encoding='utf-8') as f:
        tokens = json.load(f)
    
    sessdata = tokens.get('sessdata')
    if not sessdata:
        print("❌ 错误: tokens.json 中缺少 sessdata")
        return False
    
    # 更新SESSDATA文件
    sessdata_info = {
        'value': sessdata,
        'updated': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S %Z')
    }
    
    with open('SESSDATA', 'w', encoding='utf-8') as f:
        f.write(json.dumps(sessdata_info, ensure_ascii=False))
    
    print("✅ SESSDATA文件已更新!")
    print(f"   SESSDATA: {sessdata}")
    print(f"   更新时间: {sessdata_info['updated']}")
    print(f"\n注意: refresh_token API 目前不可用，请定期运行 login.py 重新登录")
    
    return True

if __name__ == "__main__":
    update_sessdata()

