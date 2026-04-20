
from presentation import stock_list, buy_sell, wallet_detail


choice=0



while (choice !=5):
    print("\Main menu: \n\t1. See list stocks\n\t2. Buy stocks\n\t3.Sell stocks\n\t4. See your stocks\n\t5.Exit")
    choice=input("Your choice: ")
    print(f"your choice is {choice} and type is {type(choice)}")
    if (choice == "1"):
        stock_list.see_all_stocks()
    elif (choice =="2"):
        buy_sell.buy_stock_by_name()
    elif (choice =="3"):
        buy_sell.sell_stock_by_name()
    elif (choice =="4"):
        wallet_detail.see_your_stocks()
    elif (choice =="5"):
        print()
    else:
        print ("Unavailable choice!!!!!!!!! What the hell")

