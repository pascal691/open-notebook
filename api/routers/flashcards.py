from typing import List

from fastapi import APIRouter, HTTPException
from loguru import logger

from api.models import (
    FlashcardDeckResponse,
    FlashcardGenerateRequest,
    FlashcardResponse,
)
from open_notebook.domain.flashcards import FlashcardDeck
from open_notebook.domain.notebook import Notebook
from open_notebook.exceptions import OpenNotebookError
from open_notebook.graphs.flashcards import graph as flashcards_graph

router = APIRouter()


def _deck_response(deck: FlashcardDeck) -> FlashcardDeckResponse:
    return FlashcardDeckResponse(
        id=deck.id or "",
        title=deck.title,
        cards=[FlashcardResponse(**c) for c in deck.cards],
        created=str(deck.created),
        updated=str(deck.updated),
    )


@router.post(
    "/notebooks/{notebook_id}/flashcard-decks", response_model=FlashcardDeckResponse
)
async def generate_flashcard_deck(notebook_id: str, request: FlashcardGenerateRequest):
    """Generate a new flashcard deck from a notebook's content."""
    try:
        notebook = await Notebook.get(notebook_id)

        context = await notebook.get_context()
        if not context.strip():
            raise HTTPException(
                status_code=400,
                detail="This notebook has no content yet. Add sources or notes first.",
            )

        result = await flashcards_graph.ainvoke(
            dict(context=context, num_cards=request.num_cards),  # type: ignore[arg-type]
            config=dict(configurable={"model_id": request.model_id}),
        )
        deck_output = result["deck"]

        deck = FlashcardDeck(
            title=deck_output.title,
            cards=[c.model_dump() for c in deck_output.cards],
        )
        await deck.save()
        await deck.add_to_notebook(notebook_id)

        return _deck_response(deck)
    except HTTPException:
        raise
    except OpenNotebookError:
        raise
    except Exception as e:
        logger.error(
            f"Error generating flashcard deck for notebook {notebook_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Flashcard generation failed: {str(e)}"
        )


@router.get(
    "/notebooks/{notebook_id}/flashcard-decks",
    response_model=List[FlashcardDeckResponse],
)
async def list_flashcard_decks(notebook_id: str):
    """List all flashcard decks generated for a notebook."""
    try:
        notebook = await Notebook.get(notebook_id)
        decks = await notebook.get_flashcard_decks()
        return [_deck_response(deck) for deck in decks]
    except HTTPException:
        raise
    except OpenNotebookError:
        raise
    except Exception as e:
        logger.error(
            f"Error listing flashcard decks for notebook {notebook_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to list flashcard decks: {str(e)}"
        )


@router.get("/flashcard-decks/{deck_id}", response_model=FlashcardDeckResponse)
async def get_flashcard_deck(deck_id: str):
    """Get a single flashcard deck by ID."""
    try:
        deck = await FlashcardDeck.get(deck_id)
        return _deck_response(deck)
    except HTTPException:
        raise
    except OpenNotebookError:
        raise
    except Exception as e:
        logger.error(f"Error fetching flashcard deck {deck_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch flashcard deck: {str(e)}"
        )


@router.delete("/flashcard-decks/{deck_id}")
async def delete_flashcard_deck(deck_id: str):
    """Delete a flashcard deck."""
    try:
        deck = await FlashcardDeck.get(deck_id)
        await deck.delete()
        return {"message": "Flashcard deck deleted successfully"}
    except HTTPException:
        raise
    except OpenNotebookError:
        raise
    except Exception as e:
        logger.error(f"Error deleting flashcard deck {deck_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete flashcard deck: {str(e)}"
        )
