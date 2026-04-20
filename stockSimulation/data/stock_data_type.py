#stock_data_type

# Kiểu dữ liệu của stock_list, stock_detail

class Stock:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity
    def __str__(self):
        return f"Stock(name='{self.name}', price={self.price}, quantity={self.quantity})"
    def get_name(self):
        return self.name
    def get_price(self):
        return self.price
    def get_quantity(self):
        return self.quantity
    def change_price(self,price):
        self.stocks.price=price


class StockList:
    def __init__(self):
        self.stocks = [
            Stock("VIC",150,3000),
            Stock("FPT", 130, 2000),
            Stock("HPG", 26, 8000),
        ]
    def add_stock(self, stock):
        self.stocks.append(stock)
    def get_stocks(self):
        return self.stocks
