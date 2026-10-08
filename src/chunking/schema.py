# The chunk schema

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class ChunkRecord:
    """
    A text chunk with its source metadata.
    """

    chunk_id: str
    text: str
    source: str
    file_name: str
    file_type: str
    page_number: Optional[int]
    chunk_index: int
    start_char: int
    end_char: int

    def to_dict(self) -> dict:
        return asdict(self)