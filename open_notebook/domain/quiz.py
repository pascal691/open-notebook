from typing import Any, ClassVar, Dict, List

from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import InvalidInputError


class Quiz(ObjectModel):
    table_name: ClassVar[str] = "quiz"
    title: str
    questions: List[Dict[str, Any]]

    async def add_to_notebook(self, notebook_id: str) -> Any:
        if not notebook_id:
            raise InvalidInputError("Notebook ID must be provided")
        return await self.relate("quiz_of", notebook_id)
