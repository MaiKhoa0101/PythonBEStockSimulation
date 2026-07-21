from datetime import datetime, timezone
import enum
import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.sql import func

from src.infrastructure.database.session import Base


class AdminAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    PATCH = "PATCH"
    DELETE = "DELETE"


class AdminActionLog(Base):
    __tablename__ = "admin_action_logs"

    id           = Column(String(50),  primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id     = Column(String(255), nullable=False,   comment="ID của Admin thực hiện thao tác")
    admin_email  = Column(String(255), nullable=True,    comment="Email Admin tại thời điểm thao tác")
    action       = Column(String(50),  nullable=False,   comment="CREATE | UPDATE | DELETE")
    movie_id     = Column(String(255), nullable=False,   comment="ID bộ phim bị tác động")
    movie_title  = Column(String(255), nullable=True,    comment="Tên phim tại thời điểm thao tác, lưu để hiển thị dễ đọc")
    old_values   = Column(Text,        nullable=True,    comment="JSON — trạng thái dữ liệu TRƯỚC khi thao tác")
    new_values   = Column(Text,        nullable=True,    comment="JSON — trạng thái dữ liệu SAU khi thao tác")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    def __repr__(self):
        return f"<AdminActionLog action={self.action!r} movie={self.movie_id!r} by={self.admin_id!r}>"