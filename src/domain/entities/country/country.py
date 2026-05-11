from dataclasses import dataclass, field
from typing import  Optional

@dataclass
class Country:
    id: str
    name: str
    slug: Optional[str] = None

