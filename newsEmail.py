import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def load_news_analysis(file_path="news_analysis.json"):
    """加载新闻分析结果"""
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在")
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载分析结果失败: {str(e)}")
        return []

def format_news_for_email(analysis_data, max_items=10):
    """格式化新闻分析结果用于邮件发送"""
    if not analysis_data:
        return "暂无最新财经新闻分析", ""
    
    # 按时间排序（最新的在前）
    sorted_data = sorted(
        analysis_data,
        key=lambda x: x["news"].get("pub_date", ""),
        reverse=True
    )
    
    # 获取最新几条
    recent_data = sorted_data[:max_items]
    
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
            .positive { color: #27ae60; }
            .negative { color: #e74c3c; }
            .link { color: #3498db; text-decoration: none; font-size: 13px; }
            .footer { margin-top: 20px; font-size: 12px; color: #95a5a6; text-align: center; }
        </style>
    </head>
    <body>
        <div class="header">📰 最新财经新闻分析报告 📰</div>
    """
    
    for i, item in enumerate(recent_data, 1):
        news = item["news"]
        analysis = item["analysis"]
        
        # 格式化时间
        pub_date = news.get("pub_date", "")
        try:
            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            formatted_date = dt.strftime("%Y-%m-%d %H:%M")
        except:
            formatted_date = pub_date[:16]
        
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
                    {stock.get('reason', '')}
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
            共 {len(recent_data)} 条分析 | 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}
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
        print("请设置环境变量: QQ_EMAIL 和 QQ_EMAIL_PASSWORD")
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

def main():
    # 1. 加载分析结果
    analysis_data = load_news_analysis()
    if not analysis_data:
        print("没有可发送的分析结果")
        return
    
    # 2. 格式化消息
    text_content, html_content = format_news_for_email(analysis_data)
    
    # 3. 设置邮件主题和接收人
    date_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"📈 财经新闻分析报告 {date_str}"
    receiver = os.environ.get("QQ_EMAIL")

    print(os.environ.get("QQ_EMAIL"))
    print(os.environ.get("QQ_EMAIL_PASSWORD"))
    
    if not receiver:
        print("未提供接收邮箱")
        return
    
    # 4. 发送邮件
    if send_email_via_qq(subject, text_content, html_content, receiver):
        print("邮件发送成功!")
    else:
        print("邮件发送失败，请检查配置")

if __name__ == "__main__":
    # 配置说明
    print("=" * 60)
    print("财经新闻邮件推送系统")
    print("=" * 60)
    print("使用前请确保:")
    print("1. 已设置QQ邮箱环境变量:")
    print("   export QQ_EMAIL=your_email@qq.com")
    print("   export QQ_EMAIL_PASSWORD=your_authorization_code")
    print("2. 授权码获取方法:")
    print("   - 登录QQ邮箱网页版")
    print("   - 设置 > 账号 > 生成授权码")
    print("=" * 60)
    print()
    
    main()