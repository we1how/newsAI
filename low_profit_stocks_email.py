import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import akshare as ak
import pandas as pd


def get_a_stocks():
    """
    检索所有A股股票（需排除科创板和创业板股票）
    """
    # 获取所有A股股票列表
    stock_list = ak.stock_info_a_code_name()
    
    # 排除科创板和创业板股票
    # 科创板股票代码以688开头，创业板股票代码以300开头
    filtered_stocks = stock_list[
        ~stock_list['code'].str.startswith('688') & 
        ~stock_list['code'].str.startswith('300')
    ]
    
    return filtered_stocks


def get_last_profit_ratio(stock_code):
    """
    获取股票在最后一个交易日的获利比例数据
    """
    try:
        # 获取股票的筹码分布数据
        stock_cyq_em_df = ak.stock_cyq_em(symbol=stock_code, adjust="")
        
        # 获取最后一个交易日的数据
        if not stock_cyq_em_df.empty:
            last_row = stock_cyq_em_df.iloc[-1]
            # 提取获利比例
            profit_ratio = last_row['获利比例']
            price = last_row['平均成本']
            return profit_ratio, price
        else:
            return None, None
    except Exception as e:
        # 如果获取数据失败，返回None
        return None, None


def filter_low_profit_stocks(stocks, threshold=0.1):
    """
    筛选并打印出获利比例低于阈值的股票信息
    """
    low_profit_stocks = []
    
    # 遍历股票列表
    for index, row in stocks.iterrows():
        stock_code = row['code']
        stock_name = row['name']
        
        # 获取最后一个交易日的获利比例
        profit_ratio, price = get_last_profit_ratio(stock_code)
        
        # 如果成功获取到获利比例且低于阈值，则添加到结果列表
        if profit_ratio is not None and profit_ratio < threshold:
            low_profit_stocks.append({
                'code': stock_code,
                'name': stock_name,
                'profit_ratio': profit_ratio,
                'price': price
            })
    
    return low_profit_stocks


def format_low_profit_stocks_for_email(low_profit_stocks):
    """
    格式化低获利比例股票信息用于邮件发送
    """
    if not low_profit_stocks:
        return "暂无低获利比例股票信息", ""
    
    # 构建纯文本内容
    text_content = ["📉 低获利比例股票信息 📉\n"]
    
    # 构建HTML内容
    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .header { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 20px; color: #1a5276; }
            .stock-item { margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
            .stock-code { font-size: 16px; font-weight: bold; color: #2c3e50; }
            .stock-info { color: #7f8c8d; font-size: 14px; }
            .footer { margin-top: 20px; font-size: 12px; color: #95a5a6; text-align: center; }
        </style>
    </head>
    <body>
        <div class="header">📉 低获利比例股票信息 📉</div>
    """
    
    for i, stock in enumerate(low_profit_stocks, 1):
        # 纯文本内容
        text_content.append(f"【{i}】{stock['name']} ({stock['code']})")
        text_content.append(f"  获利比例: {stock['profit_ratio']:.4f} | 价格: {stock['price']}")
        text_content.append("")
        
        # HTML内容
        html_content += f"""
        <div class="stock-item">
            <div class="stock-code">【{i}】{stock['name']} ({stock['code']})</div>
            <div class="stock-info">获利比例: {stock['profit_ratio']:.4f} | 价格: {stock['price']}</div>
        </div>
        """
    
    # 添加页脚
    html_content += f"""
        <div class="footer">
            共 {len(low_profit_stocks)} 只股票 | 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}
        </div>
    </body>
    </html>
    """
    
    return "\n".join(text_content), html_content


def send_email_via_qq(subject, text_content, html_content, receivers):
    """
    通过QQ邮箱发送邮件给多个收件人
    """
    # 邮箱配置
    smtp_server = "smtp.qq.com"
    port = 587  # QQ邮箱TLS端口
    
    # 从环境变量获取邮箱和授权码
    email_user = os.environ.get("QQ_EMAIL")
    email_password = os.environ.get("QQ_EMAIL_PASSWORD")
    
    if not email_user or not email_password:
        print("未设置QQ邮箱或授权码环境变量")
        return False
    
    # 确保receivers是列表格式
    if isinstance(receivers, str):
        receivers = [receivers]
    
    # 创建邮件
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_user
    msg["To"] = ", ".join(receivers)  # 多个收件人用逗号分隔
    
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
        
        # 发送邮件给所有收件人
        server.sendmail(email_user, receivers, msg.as_string())
        server.quit()
        
        print(f"邮件已发送至: {', '.join(receivers)}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return False


def send_low_profit_stocks_email():
    """
    发送低获利比例股票邮件给多个收件人
    """
    # 1. 获取A股股票列表
    a_stocks = get_a_stocks()
    print(f"总共获取到 {len(a_stocks)} 只A股股票（已排除科创板和创业板）")
    
    # 为了提高测试速度，只处理前100只股票
    # 在实际使用中，可以移除这个限制
    test_stocks = a_stocks.head(100)
    
    # 2. 筛选获利比例低于10%的股票
    low_profit_stocks = filter_low_profit_stocks(test_stocks, 0.1)
    
    # 3. 格式化消息
    text_content, html_content = format_low_profit_stocks_for_email(low_profit_stocks)
    
    # 4. 设置邮件主题和接收人
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"📉 低获利比例股票信息 {date_str}"
    
    # 从环境变量获取收件人列表（用逗号分隔）
    receivers_env = os.environ.get("QQ_EMAIL_RECEIVERS", "")
    if not receivers_env:
        print("未设置接收邮箱列表")
        return False
    
    # 分割收件人列表
    receivers = [email.strip() for email in receivers_env.split(",") if email.strip()]
    
    if not receivers:
        print("没有有效的收件人邮箱")
        return False
    
    # 5. 发送邮件
    if send_email_via_qq(subject, text_content, html_content, receivers):
        print("邮件发送成功!")
        return True
    return False


def main():
    """
    主函数，支持定时运行
    """
    # 配置环境变量
    os.environ['QQ_EMAIL'] = '2698470157@qq.com'
    os.environ['QQ_EMAIL_PASSWORD'] = 'nrpwfrrkraagdgig'  # 替换为实际的授权码
    os.environ['QQ_EMAIL_RECEIVERS'] = '2698470157@qq.com,1912315401@qq.com'
    
    # 配置说明
    print("=" * 60)
    print("低获利比例股票邮件推送系统")
    print("=" * 60)
    
    # 首次立即发送
    if send_low_profit_stocks_email():
        print("邮件发送成功!")
    else:
        print("邮件发送失败")
    
    # # 每天运行一次
    # while True:
    #     next_run = time.time() + 86400  # 24小时
    #     print(f"\n下次运行时间: {datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M')}")
    #     time.sleep(86400)  # 等待24小时
        
    #     print("\n开始新一轮低获利比例股票信息收集与发送...")
    #     if send_low_profit_stocks_email():
    #         print("邮件发送成功!")
    #     else:
    #         print("没有新内容或邮件发送失败")


if __name__ == "__main__":
    main()