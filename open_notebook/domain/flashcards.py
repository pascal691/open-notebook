from typing import Any, ClassVar, Dict, List

from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import InvalidInputError


class FlashcardDeck(ObjectModel):
    table_name: ClassVar[str] = "flashcard_deck"
    title: str
    cards: List[Dict[str, Any]]

    async def add_to_notebook(self, notebook_id: str) -> Any:
        if not notebook_id:
            raise InvalidInputError("Notebook ID must be provided")
        return await self.relate("flashcard_deck_of", notebook_id)
