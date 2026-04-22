

def see_all_stocks():
    choice=0
    while (True):
        print("\n\nOption: \n\t1. See all stocks\n\t2. See details of stock by name\n\t3. Back to main menu")
        choice=int(input("Your choice: "))
        if (choice ==1):
            for i in getListIndexAvailable():
                print(i)
        elif (choice ==2):
            name = input("Enter stock name: ")
            see_details_of_stock_by_name(name)
        elif (choice ==3):
            break
        else:
            print ("Unavailable choice!!!!!!!!! What the hell")



from src.domain.entities import stocks
stockList = stocks.StockList

def see_details_of_stock_by_name(name):
    stock = getMovieWithName(stockList,name)
    if (stock):
        print(f"Details for stock '{stock.name}': {getMovieWithName(stockList,name)}")
    else:
        print(f"Stock '{name}' not found in the list.")
    
