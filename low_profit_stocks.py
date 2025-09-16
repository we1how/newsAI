import akshare as ak

# stock_cyq_em_df = ak.stock_cyq_em(symbol="000507", adjust="").iloc[-1]
# # 获取最后一个交易日的数据
# last_row = stock_cyq_em_df
# # 提取获利比例和价格
# profit_ratio = last_row['获利比例']
# price = last_row['平均成本']
# # 打印结果
# print(f"最后一个交易日的获利比例: {profit_ratio}, 价格: {price}")

# stock_list = ak.stock_info_a_code_name()
# # 排除科创板和创业板股票
# #     科创板股票代码以688开头，创业板股票代码以300开头
# filtered_stocks = stock_list[
#     ~stock_list['code'].str.startswith('688') & 
#     ~stock_list['code'].str.startswith('300')
# ]

# # 写入结果到1.txt
# filtered_stocks.to_csv('1.txt', index=False, sep='\t', encoding='utf-8')

# print(filtered_stocks)


from china_stock_data import StockData

# 测试获取单只股票的筹码分布数据
stock_code = "000001"  # 平安银行
try:
    stock = StockData(stock_code)
    chip_data = stock.get_data("chip")
    print(f"股票 {stock_code} 的筹码分布数据:")
    print(chip_data)
    if not chip_data.empty:
        last_row = chip_data.iloc[-1]
        print(f"数据列名: {list(last_row.index)}")
        print(f"最新获利比例: {last_row.get('获利比例', 'N/A')}")
        print(f"平均成本: {last_row.get('平均成本', 'N/A')}")
except Exception as e:
    print(f"获取股票 {stock_code} 数据时出错: {e}")