from src.infrastructure.database.repositories import stock_repository


def getIndexWithName(stockList,name):
    return stock_repository.getIndexWithNameRepo(stockList,name)

def getListIndexAvailable():
    return stock_repository.getListIndexAvailableRepo()
