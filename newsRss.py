import os
import json
import requests
import feedparser
from bs4 import BeautifulSoup
import html
import time
import re
import random
from datetime import datetime, timezone

# 全局配置文件路径
LINKS_FILE = "analyzed_links.json"

# 随机用户代理列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
]

def get_random_user_agent():
    """获取随机用户代理"""
    return random.choice(USER_AGENTS)

def clean_html_content(html_content):
    """使用BeautifulSoup清理HTML内容并提取纯文本"""
    if not html_content:
        return ""
    
    try:
        # 先解码HTML实体
        decoded_content = html.unescape(html_content)
        
        # 使用BeautifulSoup解析
        soup = BeautifulSoup(decoded_content, 'html.parser')
        
        # 移除不需要的元素
        for element in soup(['script', 'style', 'img', 'a', 'br', 'iframe', 'object']):
            element.decompose()
        
        # 获取纯净文本
        text = soup.get_text(separator='\n', strip=True)
        
        # 清理多余空格和空行
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    except Exception as e:
        print(f"HTML清理错误: {str(e)}")
        # 回退方法：使用正则表达式移除HTML标签
        return re.sub(r'<[^>]+>', '', html_content)

def fetch_rss_content(rss_url):
    """直接获取RSS内容，绕过Cloudflare防护"""
    max_retries = 3
    retry_delay = 5  # 增加延迟时间
    
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': 'application/rss+xml, application/xml; q=0.9, */*; q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Referer': 'https://www.google.com/',
                'DNT': '1',
            }
            
            # 添加随机延迟避免被识别为爬虫
            time.sleep(random.uniform(1.0, 3.0))
            
            response = requests.get(rss_url, headers=headers, timeout=15)
            
            # 检查状态码
            if response.status_code != 200:
                print(f"HTTP错误: {response.status_code}")
                if response.status_code == 403:
                    print("Cloudflare防护已触发，尝试绕过...")
                continue
            
            # 检查内容是否是RSS
            if not response.text.strip().startswith('<?xml') and '<rss' not in response.text:
                print("响应内容不是有效的RSS XML")
                continue
                
            return response.text
        
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                print(f"{retry_delay}秒后重试...")
                time.sleep(retry_delay)
    
    return None

def parse_rss_feed(xml_content):
    """解析RSS XML内容"""
    try:
        feed = feedparser.parse(xml_content)
        
        if feed.bozo:
            print(f"解析警告: {feed.bozo_exception}")
            
            # 尝试修复常见实体问题
            if 'undefined entity' in str(feed.bozo_exception):
                fixed_content = xml_content.replace('&nbsp;', ' ')
                fixed_content = fixed_content.replace('&amp;', '&')
                fixed_content = fixed_content.replace('&lt;', '<')
                fixed_content = fixed_content.replace('&gt;', '>')
                feed = feedparser.parse(fixed_content)
        
        return feed
    
    except Exception as e:
        print(f"解析RSS失败: {str(e)}")
        return None

def load_analyzed_links():
    """加载已分析的链接"""
    if not os.path.exists(LINKS_FILE):
        return {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "links": []
        }
    
    try:
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载链接文件失败: {str(e)}")
        return {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "links": []
        }

def save_analyzed_links(link_data):
    """保存已分析的链接"""
    with open(LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(link_data, f, ensure_ascii=False, indent=2)

def fetch_cls_news(rss_url):
    """从财联社RSS源获取新闻并过滤已分析的"""
    xml_content = fetch_rss_content(rss_url)
    if not xml_content:
        print("无法获取RSS内容")
        return []
    
    feed = parse_rss_feed(xml_content)
    if not feed or not hasattr(feed, 'entries'):
        print("解析RSS源失败")
        return []
    
    # 加载已分析的链接
    link_data = load_analyzed_links()
    analyzed_links = set(link_data["links"])
    
    # 收集新新闻
    new_news = []
    
    for entry in feed.entries:
        # 获取基本元数据
        title = entry.get('title', '无标题')
        pub_date = entry.get('published', '未知时间')
        author = entry.get('author', '未知作者')
        link = entry.get('link', '')
        
        # 跳过已分析的链接
        if link in analyzed_links:
            continue
        
        # 特殊处理description字段
        raw_description = entry.get('description', '')
        clean_description = clean_html_content(raw_description)
        
        # 提取新闻来源（财联社特定格式）
        source_match = re.search(r'财联社(\d+月\d+日)?[讯|电]', clean_description)
        source = source_match.group(0) if source_match else "财联社"
        
        # 提取新闻正文（去除来源行）
        content = re.sub(r'^财联社.*?[讯|电]', '', clean_description, count=1).strip()
        
        new_news.append({
            'title': title,
            'content': content,
            'source': source,
            'pub_date': pub_date,
            'author': author,
            'link': link
        })
    
    return new_news[:5]

def mark_links_as_analyzed(links):
    """标记链接为已分析"""
    link_data = load_analyzed_links()
    
    # 添加新链接
    for link in links:
        if link not in link_data["links"]:
            link_data["links"].append(link)
    
    # 更新最后更新时间
    link_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    # 保存
    save_analyzed_links(link_data)

if __name__ == "__main__":
    RSS_URL = "https://rsshub.app/cls/depth/1000"
    
    print("正在获取财联社新闻，可能需要一些时间...")
    news_data = fetch_cls_news(RSS_URL)
    print(f"获取到 {len(news_data)} 条新新闻")