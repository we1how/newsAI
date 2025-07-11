import json
import pandas as pd
from datetime import datetime, timedelta
import os

def json_to_excel(json_file, excel_file):
    """
    将JSON分析结果转换为Excel格式并追加到现有文件
    
    参数:
    json_file: JSON文件路径
    excel_file: Excel文件路径
    """
    # 读取JSON数据
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取JSON文件失败: {str(e)}")
        return
    
    # 定义表格列名（包含三个日期表现列）
    columns = [
        '序号', '新闻总结', '新闻链接', '股票', '利空/利好', 
        '初始价格', '当日表现', '次日表现', '三日表现', '新闻日期'
    ]
    
    # 如果Excel文件不存在，创建带表头的新文件
    if not os.path.exists(excel_file):
        df_new = pd.DataFrame(columns=columns)
        df_new.to_excel(excel_file, index=False)
        print(f"创建新的Excel文件: {excel_file}")
    
    # 读取现有Excel数据
    try:
        df_existing = pd.read_excel(excel_file)
    except Exception as e:
        print(f"读取Excel文件失败: {str(e)}")
        return
    
    # 确定下一个序号
    start_index = df_existing['序号'].max() + 1 if not df_existing.empty else 1
    
    # 准备新数据列表
    new_rows = []
    
    # 处理每条新闻
    for item in data:
        # 提取新闻信息
        news_summary = item['analysis'].get('summary', '')
        news_link = item['news'].get('link', '')
        analyzed_at = item.get('analyzed_at', '')
        
        # 解析日期并计算三个表现日期
        if analyzed_at:
            try:
                # 尝试解析ISO格式日期
                date_obj = datetime.fromisoformat(analyzed_at.replace('Z', '+00:00'))
                news_date = date_obj.strftime('%Y-%m-%d')
                
                # 计算三个表现日期
                day1_date = date_obj.strftime('%Y-%m-%d')  # 当日表现
                day2_date = (date_obj + timedelta(days=1)).strftime('%Y-%m-%d')  # 次日表现
                day3_date = (date_obj + timedelta(days=2)).strftime('%Y-%m-%d')  # 三日表现
            except:
                # 简单分割日期部分作为回退
                base_date = analyzed_at.split('T')[0]
                news_date = base_date
                day1_date = base_date
                
                # 尝试计算后续日期（简单方法）
                try:
                    base_dt = datetime.strptime(base_date, '%Y-%m-%d')
                    day2_date = (base_dt + timedelta(days=1)).strftime('%Y-%m-%d')
                    day3_date = (base_dt + timedelta(days=2)).strftime('%Y-%m-%d')
                except:
                    day2_date = ""
                    day3_date = ""
        else:
            news_date = ""
            day1_date = ""
            day2_date = ""
            day3_date = ""
        
        # 处理每个股票分析
        for stock_analysis in item['analysis'].get('analysis', []):
            stock = stock_analysis.get('stock', '')
            impact = stock_analysis.get('impact', '')
            
            # 创建新行
            new_row = {
                '序号': start_index,
                '新闻总结': news_summary,
                '新闻链接': news_link,
                '股票': stock,
                '利空/利好': impact,
                '初始价格': '',  # 留空
                '当日表现': day1_date,  # 新闻分析当天日期
                '次日表现': day2_date,  # 第二天日期
                '三日表现': day3_date,  # 第三天日期
                '新闻日期': news_date  # 原始新闻日期
            }
            
            new_rows.append(new_row)
            start_index += 1  # 递增序号
    
    if not new_rows:
        print("没有新数据需要添加")
        return
    
    # 创建新数据的DataFrame
    df_new = pd.DataFrame(new_rows, columns=columns)
    
    # 合并新旧数据
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    
    # 保存到Excel
    try:
        df_combined.to_excel(excel_file, index=False)
        print(f"成功添加 {len(new_rows)} 条新记录到 {excel_file}")
    except Exception as e:
        print(f"保存Excel文件失败: {str(e)}")

if __name__ == "__main__":
    # 配置文件路径
    JSON_FILE = "news_analysis.json"
    EXCEL_FILE = "新闻股票跟踪.xlsx"
    
    # 执行转换
    json_to_excel(JSON_FILE, EXCEL_FILE)