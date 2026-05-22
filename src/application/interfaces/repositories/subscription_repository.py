from typing import List, Optional, Protocol

from src.domain.entities.subscription.subscription import Subscription
from src.infrastructure.database.models.subscription.subscription_model import SubscriptionPackageModel


class ISubscriptionRepository(Protocol):
    async def get_all_packages(self) -> List[SubscriptionPackageModel]: 
        ...
    async def get_package_by_id(self, package_id: str) -> Optional[SubscriptionPackageModel]: 
        ...
    async def create_subscription_packages(self,subscription_entity:Subscription):
        ...
    async def update_subscription_packages(self, subscription_entity: Subscription):
        ...
        