from abc import ABC, abstractmethod
from typing import Any, Dict
from app.models.invoice import InvoicePayload

class BaseERPAdapter(ABC):
    """
    Abstract base class for all ERP adapters.
    Each specific ERP (Oracle, SAP, D365, etc.) must implement its own adapter
    to extract data from its native format and yield the highly normalized
    InvoicePayload intended for the PINT AE Verification Engine.
    """
    @abstractmethod
    def transform(self, raw_data: Any) -> InvoicePayload:
        """
        Parses and maps ERP specific layout to InvoicePayload.
        """
        pass
