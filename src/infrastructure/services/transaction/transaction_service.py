
from src.presentation.dtos.user_dto import UserResponseDTO, UserUpdateDTO
from src.application.interfaces.services.users_service_interface import IGetUserById, IUpdateUser
from src.application.interfaces.repositories.subscription_repository import ISubscriptionRepository
from src.infrastructure.database.utils.mapping import dto_to_entity
from src.presentation.dtos.transaction_dto import TransactionCreateDTO, TransactionResponseDTO
from src.domain.entities.transaction.transaction import Transaction
from src.application.interfaces.repositories.transaction_repository import ITransactionRepository
from src.application.interfaces.services.transaction_service import ITransactionService

from datetime import datetime, timedelta

class TransactionService(ITransactionService):
    def __init__(
        self, 
        transaction_repository:ITransactionRepository, 
        subscription_repository:ISubscriptionRepository,
        user_update:IUpdateUser,
        user_get_by_id:IGetUserById
    ):
        self.transaction_repository=transaction_repository
        self.subscription_repository=subscription_repository
        self.user_update = user_update
        self.user_get_by_id= user_get_by_id
    
    async def create_transaction(self,transaction:TransactionCreateDTO):
        transaction = dto_to_entity(transaction,Transaction)
        result = await self.transaction_repository.create_transaction(transaction)
        return result
    
    async def read_transaction_by_id_user(self,id:str):
        result = await self.transaction_repository.read_transaction_by_id_user(id)
        return result
    
    async def read_transaction_by_id_package(self,id:str):
        result = await self.transaction_repository.read_transaction_by_id_package(id)
        return result
    
    async def read_transaction_by_id_self(self,id:str):
        print("zo service")

        result = await self.transaction_repository.read_transaction_by_id_self(id)
        return result
    
    
    async def buy_subscription_package(self, user_id, package_id):
        print("vao duoc service")
        package = await self.subscription_repository.get_package_by_id(package_id)
        if not package:
            raise Exception("Gói cước không tồn tại!")

        new_transaction = Transaction(
            amount=package.price,
            status="PENDING",
            user_id=user_id,
            package_id=package_id
        )
        saved_transaction = await self.transaction_repository.create_transaction(new_transaction)

        current_user:UserResponseDTO = await self.user_get_by_id.get_user_by_id(user_id)
        
        now = datetime.utcnow()
        base_date = (
            current_user.premium_until
            if current_user.premium_until and current_user.premium_until > now
            else now
        )
        new_premium_until = base_date + timedelta(days=package.duration_days)
        user_data = UserUpdateDTO(premium_until=new_premium_until)
        print("KQ sau khi gan: ",user_data)
        result_update_user  = await self.user_update.update_user(user_id, user_data)

        return saved_transaction