#The document schema
# To make every extracted piece of text to carry metadata
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class DocumentRecord:
    """
    Represents extracted text from a source document.
    """

    text: str
    source: str
    file_name: str
    file_type: str
    page_number: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)