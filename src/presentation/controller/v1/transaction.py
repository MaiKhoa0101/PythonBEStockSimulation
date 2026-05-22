from fastapi import APIRouter, Depends

from src.presentation.dtos.transaction_dto import TransactionCreateDTO
from src.application.interfaces.services.transaction_service import ITransactionService
from src.presentation.dtos.subscription_dto import SubscriptionCreateDTO, SubscriptionUpdateDTO
from src.presentation.controller.dependencies import ISubscriptionServiceDependency, ITransactionServiceDependency
from src.application.interfaces.services.subscription_service import ISubscriptionService


router = APIRouter()

@router.get("/{id}")
async def get_transactions_by_id(
    id:str,
    transaction_service: ITransactionService = Depends(ITransactionServiceDependency)
):
    print("zo day")
    result = await transaction_service.read_transaction_by_id_self(id)
    return result

@router.post("/create")
async def create_transaction(
    transaction: TransactionCreateDTO,
    transaction_service: ITransactionService = Depends(ITransactionServiceDependency)
):
    result = await transaction_service.create_transaction(transaction)
    return result


@router.get("/user/{id}")
async def get_transactions_by_id_user(
    id:str,
    transaction_service: ITransactionService = Depends(ITransactionServiceDependency)
):
    result = await transaction_service.read_transaction_by_id_user(id)
    return result

@router.get("/packages/{id}")
async def get_transactions_by_id_packages(
    id:str,
    transaction_service: ITransactionService = Depends(ITransactionServiceDependency)
):
    result = await transaction_service.read_transaction_by_id_package(id)
    return result

