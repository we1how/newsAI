import pandas as pd
import requests
import json
from datetime import datetime
import time
import random

def fetch_cls_headline_news():
    """获取财联社头条新闻（更新版）"""
    # 随机用户代理
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
    ]
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': 'https://www.cls.cn/',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Origin': 'https://www.cls.cn',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }
    
    # 更新后的财联社头条新闻API
    url = "https://www.cls.cn/nodeapi/telegraphList"
    
    # 请求参数
    params = {
        'app': 'CailianpressWeb',
        'category': '',
        'hasFirstVipArticle': '1',
        'lastTime': str(int(time.time())),  # 当前时间戳
        'os': 'web',
        'rn': '20',
        'sv': '7.7.5',
        'sign': ''.join(random.choices('abcdef0123456789', k=32))  # 随机生成32位签名
    }
    
    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=15
        )
        
        if response.status_code != 200:
            print(f"请求失败: HTTP {response.status_code}")
            return []
        
        data = response.json()
        
        # 解析新闻数据
        news_list = []
        for item in data.get('data', {}).get('roll_data', []):
            # 提取基本信息
            title = item.get('title', '')
            content = item.get('content', '')
            source = item.get('source_name', '财联社')
            
            # 修正链接格式
            link = f"https://www.cls.cn/detail/{item.get('id', '')}"
            
            # 处理发布时间
            timestamp = item.get('ctime', 0)
            pub_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else ''
            
            # 添加到结果列表
            news_list.append({
                'title': title,
                'content': content,
                'source': source,
                'pub_date': pub_date,
                'link': link
            })
        
        return news_list
    
    except Exception as e:
        print(f"获取财联社头条新闻失败: {str(e)}")
        return []

# 示例用法
if __name__ == "__main__":
    print("正在获取财联社头条新闻...")
    headlines = fetch_cls_headline_news()
    
    if headlines:
        print(f"获取到 {len(headlines)} 条头条新闻:")
        for i, news in enumerate(headlines, 1):
            print(f"{i}. {news['title']}")
            print(f"   发布时间: {news['pub_date']}")
            print(f"   来源: {news['source']}")
            print(f"   链接: {news['link']}")
            print("-" * 80)
    else:
        print("未获取到新闻数据")