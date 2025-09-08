import akshare as ak

stock_cyq_em_df = ak.stock_cyq_em(symbol="000507", adjust="")
# 获取最后一个交易日的数据
last_row = stock_cyq_em_df.iloc[-1]
# 提取获利比例和价格
profit_ratio = last_row['获利比例']
price = last_row['平均成本']
# 打印结果
print(f"最后一个交易日的获利比例: {profit_ratio}, 价格: {price}")