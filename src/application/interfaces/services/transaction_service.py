from typing import Protocol

from src.presentation.dtos.transaction_dto import TransactionCreateDTO


class ITransactionService(Protocol):
    async def create_transaction(transaction:TransactionCreateDTO):
        ...
    async def read_transaction_by_id_user(id:str):
        ...
    async def read_transaction_by_id_package(id:str):
        ...
    async def read_transaction_by_id_self(id:str):
        ...