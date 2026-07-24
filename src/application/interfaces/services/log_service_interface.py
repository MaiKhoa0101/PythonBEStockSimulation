
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional, Protocol


class ILogService(Protocol):
    async def fetch_list(
        self,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        name: Optional[str] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        updated_from: Optional[datetime] = None,
        updated_to: Optional[datetime] = None,
    ) -> dict:
            """
            Lấy danh sách CeleryTaskLog có phân trang, kèm filter tuỳ chọn.

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

    async def fetch_detail(self, task_id: str) -> Optional[dict]:
        """
        Lấy chi tiết đầy đủ 1 task log, bao gồm args/kwargs đã parse JSON
        và error stack trace đầy đủ. Trả None nếu không tìm thấy.
        """
        raise NotImplementedError

    async def fetch_status_summary(self) -> Dict[str, int]:
        """
        Đếm số lượng task theo từng trạng thái.
        Ví dụ: {"SUCCESS": 120, "FAILURE": 3, "RETRY": 1, "STARTED": 2, "PENDING": 0}
        """
        raise NotImplementedError