import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import news_analyzer  # 导入分析模块
import stock2csv

def format_news_for_email(analysis_data):
    """格式化新闻分析结果用于邮件发送"""
    if not analysis_data:
        return "暂无最新财经新闻分析", ""
    
    # 构建纯文本内容
    text_content = ["📰 最新财经新闻分析报告 📰\n"]
    
    # 构建HTML内容
    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .header { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 20px; color: #1a5276; }
            .news-item { margin-bottom: 25px; border-bottom: 1px solid #eee; padding-bottom: 15px; }
            .news-title { font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 5px; }
            .news-meta { color: #7f8c8d; font-size: 13px; margin-bottom: 8px; }
            .summary { margin-bottom: 10px; color: #34495e; }
            .stock-list { margin-left: 15px; }
            .stock-item { margin-bottom: 5px; }
            .positive { color: #e74c3c; }
            .negative { color: #27ae60; }
            .link { color: #3498db; text-decoration: none; font-size: 13px; }
            .footer { margin-top: 20px; font-size: 12px; color: #95a5a6; text-align: center; }
        </style>
    </head>
    <body>
        <div class="header">📰 实时财经新闻分析报告 📰</div>
    """
    
    for i, item in enumerate(analysis_data, 1):
        news = item["news"]
        analysis = item["analysis"]
        
        # 格式化时间
        pub_date = news.get("pub_date", "")
        # 增加8小时时区偏移
        try:
            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            dt = dt + timedelta(hours=8)
            formatted_date = dt.strftime("%Y-%m-%d %H:%M")
        except:
            formatted_date = pub_date[:16]
        # try:
        #     dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
        #     formatted_date = dt.strftime("%Y-%m-%d %H:%M")
        # except:
        #     formatted_date = pub_date[:16]
        
        # 纯文本内容
        text_content.append(f"【{i}】{news['title']}")
        text_content.append(f"  时间: {formatted_date} | 作者: {news.get('author', '未知作者')}")
        text_content.append(f"  总结: {analysis.get('summary', '')}")
        
        # 股票影响分析
        stock_analysis = analysis.get("analysis", [])
        if stock_analysis:
            text_content.append("  影响股票:")
            for stock in stock_analysis:
                symbol = "↑" if "利好" in stock.get("impact", "") else "↓"
                text_content.append(f"    {symbol} {stock.get('stock', '')}: {stock.get('reason', '')}")
        else:
            text_content.append("  未识别到具体股票影响")
        
        text_content.append(f"  原文: {news.get('link', '')}")
        text_content.append("")
        
        # HTML内容
        html_content += f"""
        <div class="news-item">
            <div class="news-title">【{i}】{news['title']}</div>
            <div class="news-meta">📅 {formatted_date} | ✍️ {news.get('author', '未知作者')}</div>
            <div class="summary"><strong>总结:</strong> {analysis.get('summary', '')}</div>
        """
        
        if stock_analysis:
            html_content += "<div><strong>影响股票:</strong></div><ul class='stock-list'>"
            for stock in stock_analysis:
                impact_class = "positive" if "利好" in stock.get("impact", "") else "negative"
                symbol = "🔴" if impact_class == "positive" else "🟢"
                html_content += f"""
                <li class='stock-item'>
                    <span class='{impact_class}'>{symbol} {stock.get('stock', '')}</span>: 
                     {stock.get("impact", "")},{stock.get('reason', '')}
                </li>
                """
            html_content += "</ul>"
        else:
            html_content += "<div>未识别到具体股票影响</div>"
        
        html_content += f"""
            <div><a href="{news.get('link', '')}" class="link">查看原文</a></div>
        </div>
        """
    
    # 添加页脚
    html_content += f"""
        <div class="footer">
            共 {len(analysis_data)} 条新闻 | 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}
        </div>
    </body>
    </html>
    """
    
    return "\n".join(text_content), html_content

def send_email_via_qq(subject, text_content, html_content, receiver):
    """通过QQ邮箱发送邮件"""
    # 邮箱配置
    smtp_server = "smtp.qq.com"
    port = 587  # QQ邮箱TLS端口
    
    # 从环境变量获取邮箱和授权码
    email_user = os.environ.get("QQ_EMAIL")
    email_password = os.environ.get("QQ_EMAIL_PASSWORD")
    
    if not email_user or not email_password:
        print("未设置QQ邮箱或授权码环境变量")
        return False
    
    # 创建邮件
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_user
    msg["To"] = receiver
    
    # 添加文本和HTML版本
    part1 = MIMEText(text_content, "plain", "utf-8")
    part2 = MIMEText(html_content, "html", "utf-8")
    msg.attach(part1)
    msg.attach(part2)
    
    try:
        # 连接服务器
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()  # 启用TLS加密
        server.login(email_user, email_password)
        
        # 发送邮件
        server.sendmail(email_user, receiver, msg.as_string())
        server.quit()
        
        print(f"邮件已发送至: {receiver}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return False

def send_news_email():
    """发送新闻邮件"""
    # 1. 分析新新闻
    print("开始分析新新闻...")
    new_analysis = news_analyzer.analyze_new_news()
    
    if not new_analysis:
        print("没有新新闻分析")
        return False
    
    # 2. 获取最新的分析结果（即刚分析的）
    latest_results = new_analysis  # 最多取5条
    
    # 3. 格式化消息
    text_content, html_content = format_news_for_email(latest_results)
    
    # 4. 设置邮件主题和接收人
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"📈 财经新闻分析报告 {date_str}"
    receiver = os.environ.get("QQ_EMAIL")
    
    if not receiver:
        print("未设置接收邮箱")
        return False
    
    # 5. 发送邮件
    if send_email_via_qq(subject, text_content, html_content, receiver):
        print("邮件发送成功!")
        return True
    return False

def main():
    os.environ['QQ_EMAIL'] = '2698470157@qq.com'
    os.environ['QQ_EMAIL_PASSWORD'] = 'nrpwfrrkraagdgig'  # 替换为实际的授权码

    JSON_FILE = "news_analysis.json"
    EXCEL_FILE = "新闻股票跟踪.xlsx"
    
    

    """主函数，支持定时运行"""
    # 配置说明
    print("=" * 60)
    print("实时财经新闻邮件推送系统")
    print("=" * 60)
    # print("使用前请确保:")
    # print("1. 已设置QQ邮箱环境变量:")
    # print("   export QQ_EMAIL=your_email@qq.com")
    # print("   export QQ_EMAIL_PASSWORD=your_authorization_code")
    # print("2. 已配置火山方舟API密钥:")
    # print("   export ARK_API_KEY=your_volcengine_api_key")
    # print("=" * 60)
    
    # 首次立即发送
    if send_news_email():
        print("邮件发送成功!")
        stock2csv.json_to_excel(JSON_FILE, EXCEL_FILE)
    else:
        print("邮件发送失败")
    
    # 每小时运行一次
    while True:
        next_run = time.time() + 7200
        print(f"\n下次运行时间: {datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M')}")
        time.sleep(7200)  # 等待1小时

        # 执行转换
        stock2csv.json_to_excel(JSON_FILE, EXCEL_FILE)

        print("\n开始新一轮新闻收集与发送...")
        if send_news_email():
            print("邮件发送成功!")
        else:
            print("没有新内容或邮件发送失败")



if __name__ == "__main__":
    main()