import random


#stocklist có dạng StockList
def change_stock_price_by_name(name, stocklist):
    #kiểm tra stocklist có stock nào có tên name không
    stock = stocklist.get_stocks_by_name(name)
    if (stock):
        stock["price"]=random.random()