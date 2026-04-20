from data import stock_repository, wallet_repository, stock_simulation

def getIndexWithName(stockList,name):
    return stock_repository.getIndexWithNameRepo(stockList,name)

def getListIndexAvailable():
    return stock_repository.getListIndexAvailableRepo()
