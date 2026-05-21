from typing import List

from sqlalchemy.orm import Session, joinedload

from src.infrastructure.database.utils.mapping import entity_to_model, model_to_entity
from src.domain.entities.subscription.subscription import Subscription
from src.infrastructure.database.models.subscription.subscription_model import SubscriptionPackageModel
from src.application.interfaces.repositories.subscription_repository import ISubscriptionRepository

class SubscriptionRepository(ISubscriptionRepository):
    def __init__(self,db: Session):
        self.db = db
    
    async def get_all_packages(self) -> List[Subscription]:
        db_subscription = self.db.query(SubscriptionPackageModel).all()

        result = [
            model_to_entity(
                db_subscription,
                Subscription
            )
            for db_subscription in db_subscription
        ]
                
        return result

    async def get_package_by_id(self, package_id: str) -> Subscription:
        db_subscription = self.db.query(SubscriptionPackageModel).filter(SubscriptionPackageModel.id == package_id).first()

        result = db_subscription

        return result

    async def create_subscription_packages(self, subscription_entity:Subscription):
        db_subscription = entity_to_model(
            subscription_entity,
            SubscriptionPackageModel
        )
        self.db.add(db_subscription)
        self.db.commit()
        self.db.refresh(db_subscription)
        
        subscription_entity.created_at=db_subscription.created_at
        subscription_entity.id=db_subscription.id
        return subscription_entity