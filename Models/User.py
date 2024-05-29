from dataclasses import dataclass
from typing import List


@dataclass
class User:
    chat_id: int
    steam_id: str
    selected_game: str
    selected_items: List[str]
