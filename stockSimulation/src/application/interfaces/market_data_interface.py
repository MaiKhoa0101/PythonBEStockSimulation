# Dùng để gợi ý code trên các IDE, 
# rất tiếc là cài trên vscode nên chưa test được nó gợi ý cái gì
from typing import Protocol, Any 

#Là cú pháp interface, I đầu tên là quy ước cho interface
class IMarketDataService(Protocol): 
    async def fetch_hose_index(self) -> Any:
        ... 
        # object ... này là ellipsis, 
        # ý nghĩa như pass,
        # có thể dùng pass, mà chat nó kêu để vậy nên kệ :)))