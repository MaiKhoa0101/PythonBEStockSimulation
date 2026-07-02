from abc import ABC, abstractmethod
from typing import Dict, Optional


class IAdminLogService(ABC):

    @abstractmethod
    async def fetch_list(
        self,
        page: int = 1,
        size: int = 20,
        action: Optional[str] = None,
        admin_id: Optional[str] = None,
        movie_id: Optional[str] = None,
    ) -> dict:
        """
        Trả về:
            {
                "total": int,
                "page": int,
                "size": int,
                "total_pages": int,
                "results": list[dict]
            }
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_detail(self, log_id: str) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_action_summary(self) -> Dict[str, int]:
        """Đếm số lượng theo từng action: CREATE / UPDATE / DELETE."""
        raise NotImplementedError