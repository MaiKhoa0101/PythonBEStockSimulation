
from src.application.interfaces.repositories.transaction_repository import ITransactionRepository
from src.domain.entities.subscription.subscription import Subscription
from src.infrastructure.database.utils.mapping import dto_to_entity
from src.presentation.dtos.subscription_dto import SubscriptionCreateDTO, SubscriptionUpdateDTO
from src.application.interfaces.repositories.subscription_repository import ISubscriptionRepository
from src.application.interfaces.services.subscription_service import ISubscriptionService

class SubscriptionService(ISubscriptionService):
    def __init__(self, subscription_repo: ISubscriptionRepository):
        self.subscription_repo= subscription_repo
    
    async def create_subscription_package(self,subscription_create_dto:SubscriptionCreateDTO):
        subscription = dto_to_entity(subscription_create_dto,Subscription)
        transaction = await self.transaction_repository.create_transaction()
        result = await self.subscription_repo.create_subscription_packages(subscription_entity=subscription)
            
        return result
    
    async def get_subscription_package(self, package_id:str):
        result =  await self.subscription_repo.get_package_by_id(package_id)
        return result


    async def get_list_subscription_packages(self):
        result =  await self.subscription_repo.get_all_packages()
        return result
    
    async def update_subscription_package(self, subscription_update_dto:SubscriptionUpdateDTO):
        subscription = dto_to_entity(subscription_update_dto, Subscription)

        result =  await self.subscription_repo.update_subscription_packages(subscription)
        return result
    
    async def delete_subscription_package(self, package_id:str):
        result = await super().delete_subscription_package(package_id)
        return result
