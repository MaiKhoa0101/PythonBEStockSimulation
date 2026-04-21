from typing import Protocol, Any

class IMarketDataService(Protocol):
    async def fetch_hose_index(self) -> Any:
        ...