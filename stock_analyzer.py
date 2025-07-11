import akshare as ak


# SH600777
stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="600777", period="daily", 
                                        start_date="20250701", end_date='20250710', adjust="")
print(stock_zh_a_hist_df)