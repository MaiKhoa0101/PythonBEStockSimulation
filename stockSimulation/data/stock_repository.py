#stock_repository
from data.stock_data_type import Stock

stocks_list_global = [
    {"name": "VIC","price": 150, "quantity": 3000},
    {"name":"FPT", "price":130,"quantity": 2000},
    {"name":"HPG", "price":26,"quantity": 8000}
]
listStock=[]
def initStockList():
    return stocks_list_global

def getListIndexAvailableRepo():
    if (listStock == []):
        for i in stocks_list_global:
            listStock.append(Stock(i["name"],i["price"],i["quantity"]))
            # print(f"Đã append {listStock[-1]}")
    return listStock

def getIndexWithNameRepo(stlist,name):
    for i in stocks_list_global:
        if (i["name"]==name):
            return Stock(i["name"],i["price"],i["quantity"])
    return None

        