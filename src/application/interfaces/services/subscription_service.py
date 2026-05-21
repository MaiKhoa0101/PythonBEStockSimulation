from typing import Optional, Protocol
from src.presentation.dtos.subscription_dto import SubscriptionCreateDTO, SubscriptionUpdateDTO

class ISubscriptionService(Protocol):
    async def create_subscription_package(
        subscription_create_dto: SubscriptionCreateDTO
    ):
        ...

    async def get_subscription_package(self, package_id: int):
        ...

    async def get_list_subscription_packages(self):
        ...

    async def update_subscription_package(
        self, 
        subscription_update_dto: SubscriptionUpdateDTO,
    ):
        ...

    async def delete_subscription_package(self, package_id: str) -> None:
        ...