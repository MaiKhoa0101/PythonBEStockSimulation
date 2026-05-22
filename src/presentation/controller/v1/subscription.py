from fastapi import APIRouter, Depends

from src.presentation.dtos.subscription_dto import SubscriptionCreateDTO, SubscriptionUpdateDTO
from src.presentation.controller.dependencies import ISubscriptionServiceDependency
from src.application.interfaces.services.subscription_service import ISubscriptionService


router = APIRouter()
@router.get("/")
async def get_all_subscription(
    subscription_service: ISubscriptionService = Depends(ISubscriptionServiceDependency)
):
    result = await subscription_service.get_list_subscription_packages()
    return result

@router.post("/create")
async def create_subscription(
    subscription: SubscriptionCreateDTO,
    subscription_service: ISubscriptionService = Depends(ISubscriptionServiceDependency)
):
    result = await subscription_service.create_subscription_package(subscription)
    return result

@router.patch("/update")
async def create_subscription(
    subscription: SubscriptionUpdateDTO,
    subscription_service: ISubscriptionService = Depends(ISubscriptionServiceDependency)
):
    result = await subscription_service.update_subscription_package(subscription)
    return result

