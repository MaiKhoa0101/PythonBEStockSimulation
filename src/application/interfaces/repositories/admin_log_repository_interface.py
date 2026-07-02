from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from src.infrastructure.database.models.admin.admin_action_log import AdminActionLog



class IAdminLogRepository(ABC):

    @abstractmethod
    def get_paginated(
        self,
        page: int,
        size: int,
        action: Optional[str] = None,
        admin_id: Optional[str] = None,
        movie_id: Optional[str] = None,
    ) -> Tuple[List[AdminActionLog], int]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, log_id: str) -> Optional[AdminActionLog]:
        raise NotImplementedError

    @abstractmethod
    def count_by_action(self) -> Dict[str, int]:
        raise NotImplementedError