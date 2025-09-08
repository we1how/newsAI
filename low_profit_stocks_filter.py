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

def main():
    """
    主函数
    """
    # 获取A股股票列表
    a_stocks = get_a_stocks()
    print(f"总共获取到 {len(a_stocks)} 只A股股票（已排除科创板和创业板）")
    
    # 为了提高测试速度，只处理前100只股票
    # 在实际使用中，可以移除这个限制
    test_stocks = a_stocks.head(100)
    
    # 筛选获利比例低于10%的股票
    low_profit_stocks = filter_low_profit_stocks(test_stocks, 0.1)
    
    # 打印结果
    print(f"\n获利比例低于10%的股票共有 {len(low_profit_stocks)} 只：")
    for stock in low_profit_stocks:
        print(f"股票代码: {stock['code']}, 股票名称: {stock['name']}, 获利比例: {stock['profit_ratio']:.4f}, 价格: {stock['price']}")

if __name__ == "__main__":
    main()