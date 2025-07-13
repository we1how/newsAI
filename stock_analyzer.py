import pandas as pd
import akshare as ak
import numpy as np
from datetime import datetime, timedelta
import re
import os
import time
import warnings
warnings.filterwarnings('ignore')

def extract_stock_code(stock_str):
    """从股票字符串中提取股票代码"""
    if not isinstance(stock_str, str):
        return None
    
    # 改进的正则表达式：匹配中文和英文括号内的代码
    matches = re.findall(r'[（(]([A-Za-z0-9\.]+)[)）]', stock_str)
    
    if matches:
        # 优先选择包含交易所后缀的代码
        for code in matches:
            if '.' in code:
                return code
        
        # 如果没有带后缀的代码，则处理第一个匹配项
        code = matches[0]
        
        # 添加交易所后缀
        if code.startswith(('6', '9')):
            return f"{code}.SH"
        elif code.startswith(('0', '3')):
            return f"{code}.SZ"
        elif code.startswith('4'):
            return f"{code}.BJ"
    
    return None

def get_stock_history(stock_code, base_date, days_before=1, days_after=10):
    """获取股票历史数据（优化版）"""
    if not stock_code or not base_date:
        return None
    
    try:
        # 确保日期是字符串格式
        if not isinstance(base_date, str):
            base_date = base_date.strftime('%Y-%m-%d')
        
        # 解析基准日期
        base_date_obj = datetime.strptime(base_date, '%Y-%m-%d')
        
        # 只处理A股（沪市、深市、北交所）
        if not (stock_code.endswith('.SH') or stock_code.endswith('.SZ') or stock_code.endswith('.BJ')):
            return None
        
        # 获取股票代码前缀（不含交易所后缀）
        base_code = stock_code.split('.')[0]
        
        # 计算日期范围
        start_date = (base_date_obj - timedelta(days=days_before)).strftime('%Y%m%d')
        end_date = (base_date_obj + timedelta(days=days_after)).strftime('%Y%m%d')
        
        # 获取股票历史数据
        if base_code.startswith(('5', '3')):  # 假设以5或3开头的是ETF基金
            stock_df = ak.fund_etf_hist_em(
            symbol=base_code, 
            adjust="",
            start_date=start_date,
            end_date=end_date
            )
        else:
            stock_df = ak.stock_zh_a_hist(
            symbol=base_code, 
            period="daily", 
            adjust="",
            start_date=start_date,
            end_date=end_date
            )
        
        if stock_df.empty:
            return None
        
        # 将日期列转换为字符串格式
        stock_df['日期'] = stock_df['日期'].astype(str)
        return stock_df
    
    except Exception as e:
        print(f"获取股票历史数据失败: {stock_code} - {base_date} - {str(e)}")
        return None

def get_price_on_date(stock_df, target_date):
    """从历史数据中获取指定日期价格"""
    if stock_df is None or target_date is None:
        return None, None
    
    try:
        # 确保日期是字符串格式
        if not isinstance(target_date, str):
            target_date = target_date.strftime('%Y-%m-%d')
        
        # 在历史数据中查找目标日期
        target_row = stock_df[stock_df['日期'] == target_date]
        
        if not target_row.empty:
            open_price = target_row['开盘'].values[0]
            close_price = target_row['收盘'].values[0]
            return open_price, close_price
        else:
            # 如果当天没有数据（休市），查找下一个交易日
            all_dates = stock_df['日期'].tolist()
            all_dates.sort()  # 确保日期排序
            
            # 找到目标日期之后的第一个交易日
            for date in all_dates:
                if date > target_date:
                    next_trading_row = stock_df[stock_df['日期'] == date]
                    if not next_trading_row.empty:
                        return next_trading_row['开盘'].values[0], next_trading_row['收盘'].values[0]
            
            # 如果找不到后续交易日，返回None
            return None, None
    
    except Exception as e:
        print(f"查询股票价格失败: {target_date} - {str(e)}")
        return None, None

def get_closest_trading_date(stock_df, base_date, days_offset):
    """获取距离基准日期最近的有效交易日"""
    if stock_df is None or base_date is None:
        return None
    
    try:
        # 确保日期是字符串格式
        if not isinstance(base_date, str):
            base_date = base_date.strftime('%Y-%m-%d')
        
        # 计算目标日期
        target_date = (datetime.strptime(base_date, '%Y-%m-%d') + timedelta(days=days_offset)).strftime('%Y-%m-%d')
        
        # 在历史数据中查找目标日期
        if target_date in stock_df['日期'].values:
            return target_date
        
        # 如果当天没有数据（休市），查找下一个交易日
        all_dates = stock_df['日期'].tolist()
        all_dates.sort()  # 确保日期排序
        
        # 找到目标日期之后的第一个交易日
        for date in all_dates:
            if date > target_date:
                return date
        
        # 如果找不到后续交易日，返回原始目标日期
        return target_date
    
    except Exception as e:
        print(f"查找交易日失败: {base_date} - 偏移 {days_offset} 天 - {str(e)}")
        return None

def calculate_performance(initial_price, current_price):
    """计算涨跌幅表现"""
    if initial_price is None or current_price is None or initial_price == 0:
        return ""
    
    change = ((current_price - initial_price) / initial_price) * 100
    print(f"计算表现: 初始价格={initial_price}, 当前价格={current_price}, 涨跌幅={change:.2f}%")
    return f"{change:.2f}%"

def update_stock_performance(excel_file):
    """更新股票表现数据（优化版）"""
    # 读取Excel文件
    if not os.path.exists(excel_file):
        print(f"Excel文件不存在: {excel_file}")
        return
    
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        print(f"读取Excel文件失败: {str(e)}")
        return
    
    if df.empty:
        print("Excel文件为空")
        return
    
    # 检查必要列是否存在
    required_cols = ['股票', '新闻日期', '初始价格', '当日表现', '次日表现', '三日表现']
    for col in required_cols:
        if col not in df.columns:
            print(f"缺少必要列: {col}")
            return
    
    # 记录更新行数
    updated_rows = 0
    today = datetime.now()
    
    # 遍历每一行
    for index, row in df.iterrows():
        # 跳过已完整填充的行
        if (not pd.isna(row['初始价格']) and 
            not pd.isna(row['当日表现']) and 
            not pd.isna(row['次日表现']) and 
            not pd.isna(row['三日表现'])):
            continue
        
        # 提取股票代码
        stock_str = row['股票']
        stock_code = extract_stock_code(stock_str)
        
        # 如果无法提取代码，跳过此行
        if not stock_code:
            continue
        
        # 获取新闻日期
        news_date = row['新闻日期']
        if pd.isna(news_date) or not news_date:
            continue
        
        # 确保日期是字符串格式
        if isinstance(news_date, pd.Timestamp):
            news_date_str = news_date.strftime('%Y-%m-%d')
        else:
            news_date_str = str(news_date)
        
        # 获取股票历史数据（新闻日期前后10天）
        stock_df = get_stock_history(stock_code, news_date_str, days_before=1, days_after=10)
        
        if stock_df is None or stock_df.empty:
            continue
        
        # 处理初始价格和当日表现
        if pd.isna(row['初始价格']) or pd.isna(row['当日表现']):
            open_price, close_price = get_price_on_date(stock_df, news_date_str)
            
            if open_price is not None:
                if pd.isna(row['初始价格']):
                    df.at[index, '初始价格'] = open_price
                    updated_rows += 1
                
                if pd.isna(row['当日表现']):
                    df.at[index, '当日表现'] = calculate_performance(open_price, close_price)
                    updated_rows += 1
        
        # 处理次日表现
        if pd.isna(row['次日表现']):
            # 获取最近的交易日日期
            next_date = get_closest_trading_date(stock_df, news_date_str, 1)
            
            if next_date:
                # 检查日期是否已过去
                next_date_obj = datetime.strptime(next_date, '%Y-%m-%d')
                
                if next_date_obj <= today:
                    # 日期已过去，获取价格
                    _, next_close = get_price_on_date(stock_df, next_date)
                    initial_price = row['初始价格']
                    
                    if next_close is not None and not pd.isna(initial_price):
                        df.at[index, '次日表现'] = calculate_performance(initial_price, next_close)
                        updated_rows += 1
                else:
                    # 日期未到，记录日期
                    df.at[index, '次日表现'] = next_date
                    updated_rows += 1
        
        # 处理三日表现
        if pd.isna(row['三日表现']):
            # 获取最近的交易日日期
            third_date = get_closest_trading_date(stock_df, news_date_str, 2)
            
            if third_date:
                # 检查日期是否已过去
                third_date_obj = datetime.strptime(third_date, '%Y-%m-%d')
                
                if third_date_obj <= today:
                    # 日期已过去，获取价格
                    _, third_close = get_price_on_date(stock_df, third_date)
                    initial_price = row['初始价格']
                    
                    if third_close is not None and not pd.isna(initial_price):
                        df.at[index, '三日表现'] = calculate_performance(initial_price, third_close)
                        updated_rows += 1
                else:
                    # 日期未到，记录日期
                    df.at[index, '三日表现'] = third_date
                    updated_rows += 1
        
        # 避免请求过于频繁
        time.sleep(0.5)
    
    if updated_rows > 0:
        # 保存更新后的Excel
        try:
            df.to_excel(excel_file, index=False)
            print(f"成功更新 {updated_rows} 行数据")
        except Exception as e:
            print(f"保存Excel文件失败: {str(e)}")
    else:
        print("没有需要更新的数据")

if __name__ == "__main__":
    # 配置文件路径
    EXCEL_FILE = "新闻股票跟踪.xlsx"
    
    # 执行更新
    update_stock_performance(EXCEL_FILE)