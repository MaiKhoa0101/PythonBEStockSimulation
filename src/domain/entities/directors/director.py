from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Director:
    id: str
    name: str
    slug: Optional[str] = None

