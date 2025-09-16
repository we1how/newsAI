from china_stock_data import StockData, StockMarket
import pandas as pd
import time
import akshare as ak

def get_a_stocks():
    """
    检索所有A股股票（需排除科创板和创业板股票）
    """
    try:
        # 使用china_stock_data获取所有A股股票列表
        # 注意: 这里需要根据实际情况调整获取股票列表的方式
        # 假设我们使用StockMarket类获取股票列表
        stock_list = ak.stock_info_a_code_name()
        
        # 排除科创板和创业板股票
        # 科创板股票代码以688开头，创业板股票代码以300开头
        filtered_stocks = stock_list[
            ~stock_list['code'].str.startswith('688') & 
            ~stock_list['code'].str.startswith('300')
        ]
        
        return filtered_stocks
    except Exception as e:
        print(f"获取股票列表时出错: {e}")
        # 返回空DataFrame
        return pd.DataFrame(columns=['code', 'name'])

def get_last_profit_ratio(stock_code):
    """
    获取股票在最后一个交易日的获利比例数据
    """
    try:
        # 使用StockData获取股票的筹码分布数据
        stock = StockData(stock_code)
        chip_data = stock.get_data("chip")
        
        # 获取最后一个交易日的数据
        if not chip_data.empty:
            last_row = chip_data.iloc[-1]
            # 提取获利比例和平均成本
            # 根据实际数据结构调整字段名
            profit_ratio = last_row.get('获利比例', 0)
            price = last_row.get('平均成本', 0)
            return profit_ratio, price
        else:
            print(f"股票 {stock_code} 无筹码分布数据")
            return None, None
    except Exception as e:
        print(f"获取股票 {stock_code} 数据时出错: {e}")
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
        
        # 添加延时，避免请求过于频繁
        time.sleep(0.05)
        
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
            print(f"找到符合条件的股票: {stock_code} {stock_name}, 获利比例: {profit_ratio:.4f}")
        else:
            # 
            # 
            # 
            # 
            # print(f"股票 {stock_code} {stock_name} 获利比例: {profit_ratio if profit_ratio is not None else 'N/A'}")
            pass
    
    return low_profit_stocks

def main():
    """
    主函数
    """
    # 获取A股股票列表
    a_stocks = get_a_stocks()
    print(f"总共获取到 {len(a_stocks)} 只A股股票（已排除科创板和创业板）")
    
    # 为了提高测试速度，只处理前20只股票
    # 在实际使用中，可以移除这个限制
    test_stocks = a_stocks.head(3000)
    
    # 筛选获利比例低于10%的股票
    low_profit_stocks = filter_low_profit_stocks(test_stocks, 0.1)
    
    # 打印结果
    print(f"\n获利比例低于10%的股票共有 {len(low_profit_stocks)} 只：")
    for stock in low_profit_stocks:
        print(f"股票代码: {stock['code']}, 股票名称: {stock['name']}, 获利比例: {stock['profit_ratio']:.4f}, 价格: {stock['price']:.2f}")

if __name__ == "__main__":
    main()