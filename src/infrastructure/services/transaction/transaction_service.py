
from src.infrastructure.database.utils.mapping import dto_to_entity
from src.presentation.dtos.transaction_dto import TransactionCreateDTO, TransactionResponseDTO
from src.domain.entities.transaction.transaction import Transaction
from src.application.interfaces.repositories.transaction_repository import ITransactionRepository
from src.application.interfaces.services.transaction_service import ITransactionService


class TransactionService(ITransactionService):
    def __init__(self, transaction_repository:ITransactionRepository):
        self.repository=transaction_repository
    
    async def create_transaction(self,transaction:TransactionCreateDTO):
        transaction = dto_to_entity(transaction,Transaction)
        result = await self.repository.create_transaction(transaction)
        return result
    async def read_transaction_by_id_user(self,id:str):
        result = await self.repository.read_transaction_by_id_user(id)
        return result
    async def read_transaction_by_id_package(self,id:str):
        result = await self.repository.read_transaction_by_id_package(id)
        return result
    async def read_transaction_by_id_self(self,id:str):
        print("zo service")

        result = await self.repository.read_transaction_by_id_self(id)
        return result