# Dùng để gợi ý code trên các IDE, 
# rất tiếc là cài trên vscode nên chưa test được nó gợi ý cái gì
from typing import Protocol, Any 

#Là cú pháp interface, I đầu tên là quy ước cho interface
class IMoviesService(Protocol): 
    async def fetch_movies_list() -> Any:
        ... 