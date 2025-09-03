import json
import time
import os
from datetime import datetime, timedelta
import requests
from wxauto import WeChat  # 用于微信自动化
import news_analyzer  # 导入分析模块
import stock2csv

import logging
logging.getLogger("httpx").setLevel(logging.WARNING)

def analyze_and_send_news():
    """分析新闻并发送到微信"""
    print("开始分析新新闻...")
    new_analysis = news_analyzer.analyze_new_news()
    
    if not new_analysis:
        print("没有新新闻分析")
        return False
    
    # 格式化消息
    message = format_news_for_wechat(new_analysis)
    print("\n格式化后的消息内容:")
    print("-" * 50)
    print(message)
    print("-" * 50)
    
    # 发送到微信
    receiver = "文件传输助手"  # 默认发送到文件传输助手
    # receiver = "专项群"
    success = send_to_wechat(message, receiver)
    
    if success:
        # 更新Excel文件
        JSON_FILE = "news_analysis.json"
        EXCEL_FILE = "新闻股票跟踪.xlsx"
        stock2csv.json_to_excel(JSON_FILE, EXCEL_FILE)
    
    return success

def format_news_for_wechat(analysis_data, max_items=5):
    """格式化新闻分析结果用于微信发送"""
    if not analysis_data:
        return "暂无最新财经新闻分析"
    
    # 构建消息内容
    messages = ["📰 分析报告 📰", ""]
    
    for i, item in enumerate(analysis_data[:max_items], 1):
        news = item["news"]
        analysis = item["analysis"]
        
        # 格式化时间
        pub_date = news.get("pub_date", "")
        try:
            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            dt = dt + timedelta(hours=8)  # 增加8小时时区偏移
            formatted_date = dt.strftime("%Y-%m-%d %H:%M")
        except:
            formatted_date = pub_date[:16] if len(pub_date) >= 16 else pub_date
        
        # 构建消息块
        messages.append(f"【{i}】{news['title']}")
        messages.append(f"  时间: {formatted_date} | 作者: {news.get('author', '未知作者')}")
        messages.append(f"  总结: {analysis.get('summary', '')}")
        
        # 添加股票影响分析
        stock_analysis = analysis.get("analysis", [])
        if stock_analysis:
            messages.append("  影响股票:")
            for stock in stock_analysis:
                symbol = "🔴" if "利好" in stock.get("impact", "") else "🟢"
                messages.append(f"    {symbol} {stock.get('stock', '')}: {stock.get('impact', '')} - {stock.get('reason', '')}")
        else:
            messages.append("  未识别到具体股票影响")
        
        messages.append(f"  原文: {news.get('link', '')}")
        messages.append("")
    
    messages.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    return "\n".join(messages)

def send_to_wechat(message, receiver):
    """通过微信发送消息"""
    try:
        # 初始化微信客户端
        wx = WeChat()
        
        # 等待微信启动
        time.sleep(2)
        
        # 发送消息
        wx.ChatWith(receiver)
        wx.SendMsg(message)
        
        print(f"消息已发送至: {receiver}")
        return True
    except Exception as e:
        print(f"微信发送失败: {str(e)}")
        return False

def main():
    """主函数，支持定时运行"""
    # 配置说明
    print("=" * 60)
    print("实时财经新闻微信推送系统")
    print("=" * 60)
    
    # 首次立即发送
    if analyze_and_send_news():
        print("微信发送成功!")
    else:
        print("没有新内容或发送失败")
    
    # 每2小时运行一次
    while True:
        next_run = time.time() + 600  # 10分钟后
        print(f"\n下次运行时间: {datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M')}")
        time.sleep(600)  # 休眠5分钟，避免频繁检查

        print("\n开始新一轮新闻收集与发送...")
        if analyze_and_send_news():
            print("微信发送成功!")
        else:
            print("没有新内容或发送失败")

if __name__ == "__main__":
    # receiver = "文件传输助手"
    # try:
    #     # 初始化微信客户端
    #     wx = WeChat()
        
    #     # 等待微信启动
    #     time.sleep(2)
        
    #     # 发送消息
    #     wx.ChatWith(receiver)
    #         # 发送消息
    #     wx.SendMsg(1111)
        
    #     print(f"消息已发送至: {receiver}")
        
    # except Exception as e:
    #     print(f"微信发送失败: {str(e)}")
        
    main()


