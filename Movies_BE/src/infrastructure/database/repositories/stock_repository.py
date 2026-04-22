#stock_repository
from src.domain.entities.stocks import Stock

stocks_list_global = [
    {"name": "VIC","price": 150, "quantity": 3000},
    {"name":"FPT", "price":130,"quantity": 2000},
    {"name":"HPG", "price":26,"quantity": 8000}
]
listStocks=[]

def initStockList():
    return stocks_list_global

def getListIndexAvailableRepo():
    global listStocks
    if (listStocks == []):
        listStocks = list(stocks_list_global)
    return listStocks

def getIndexWithNameRepo(stlist,name):
    for i in stocks_list_global:
        if (i["name"]==name):
            return Stock(i["name"],i["price"],i["quantity"])
    return None

        