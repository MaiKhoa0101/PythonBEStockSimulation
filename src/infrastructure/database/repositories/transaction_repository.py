from sqlalchemy.orm import Session, joinedload

from src.infrastructure.database.models.transaction.transaction_model import TransactionModel
from src.domain.entities.transaction.transaction import Transaction
from src.infrastructure.database.utils.mapping import entity_to_model, model_to_entity
from src.application.interfaces.repositories.transaction_repository import ITransactionRepository


class TransactionRepository(ITransactionRepository):
    def __init__(self,db: Session):
        self.db = db
    async def create_transaction(self,transaction:Transaction):
        db_transaction = entity_to_model(
            transaction,
            TransactionModel
        )
        self.db.add(db_transaction)
        self.db.commit()
        self.db.refresh(db_transaction)

        transaction.id = db_transaction.id
        transaction.created_at=db_transaction.created_at
        transaction.status=db_transaction.status
        
        return transaction
    
    async def read_transaction_by_id_user(self,id:str):
        db_transaction = self.db.query(
                TransactionModel
                ).filter(
                TransactionModel.user_id==id
                ).all()
        result = [
            model_to_entity(
                db_transaction,
                Transaction
            )
            for db_transaction in db_transaction
        ]
        return result
    
    async def read_transaction_by_id_package(self,id:str):
        db_transaction = self.db.query(
                TransactionModel
                ).filter(
                TransactionModel.package_id==id
                ).all()
        result = [
            model_to_entity(
                db_transaction,
                Transaction
            )
            for db_transaction in db_transaction
        ]
        return result
    async def read_transaction_by_id_self(self,id:str):
        print("zo repo")

        db_transaction = self.db.query(
                TransactionModel
            ).filter(
            TransactionModel.id==id
            ).first()
        
        if not db_transaction:
            return None
        result = model_to_entity(
            db_transaction,
            Transaction
        )
        return result