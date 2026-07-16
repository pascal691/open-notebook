"""
Unit tests for the quiz and flashcards API routers.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from open_notebook.domain.flashcards import FlashcardDeck
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.quiz import Quiz
from open_notebook.exceptions import NotFoundError


@pytest.fixture
def client():
    """Create test client after environment variables have been cleared by conftest."""
    from api.main import app

    return TestClient(app)


class _FakeQuizQuestion(BaseModel):
    question: str = "Q1?"
    options: list = ["A", "B", "C", "D"]
    correct_answer_index: int = 1
    explanation: str = "Because B."


class _FakeQuizOutput(BaseModel):
    title: str = "Generated Quiz"
    questions: list = [_FakeQuizQuestion()]


class _FakeFlashcard(BaseModel):
    front: str = "RAG"
    back: str = "Retrieval-Augmented Generation"


class _FakeDeckOutput(BaseModel):
    title: str = "Generated Deck"
    cards: list = [_FakeFlashcard()]


class TestQuizRouter:
    """Test suite for the quiz generation/list/get/delete endpoints."""

    def test_generate_quiz_notebook_not_found(self, client):
        with patch.object(
            Notebook, "get", new=AsyncMock(side_effect=NotFoundError("not found"))
        ):
            response = client.post(
                "/api/notebooks/notebook:missing/quizzes",
                json={"num_questions": 5},
            )

        assert response.status_code == 404

    def test_generate_quiz_empty_notebook_returns_400(self, client):
        notebook = Notebook(id="notebook:test", name="Test", description="Test")

        with (
            patch.object(Notebook, "get", new=AsyncMock(return_value=notebook)),
            patch.object(Notebook, "get_context", new=AsyncMock(return_value="   ")),
        ):
            response = client.post(
                "/api/notebooks/notebook:test/quizzes",
                json={"num_questions": 5},
            )

        assert response.status_code == 400

    def test_generate_quiz_success(self, client):
        notebook = Notebook(id="notebook:test", name="Test", description="Test")

        async def fake_ainvoke(payload, config=None):
            return {"quiz": _FakeQuizOutput()}

        async def fake_save(self):
            self.id = "quiz:new"
            self.created = "2024-01-01T00:00:00"
            self.updated = "2024-01-01T00:00:00"

        with (
            patch.object(Notebook, "get", new=AsyncMock(return_value=notebook)),
            patch.object(
                Notebook, "get_context", new=AsyncMock(return_value="Some content")
            ),
            patch("api.routers.quiz.quiz_graph.ainvoke", new=fake_ainvoke),
            patch.object(Quiz, "save", new=fake_save),
            patch.object(Quiz, "add_to_notebook", new=AsyncMock(return_value=True)),
        ):
            response = client.post(
                "/api/notebooks/notebook:test/quizzes",
                json={"num_questions": 3},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Generated Quiz"
        assert len(data["questions"]) == 1
        assert data["questions"][0]["correct_answer_index"] == 1

    def test_list_quizzes(self, client):
        notebook = Notebook(id="notebook:test", name="Test", description="Test")
        quiz = Quiz(
            id="quiz:1",
            title="Existing Quiz",
            questions=[
                {
                    "question": "Q?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer_index": 0,
                    "explanation": "Because A.",
                }
            ],
        )

        with (
            patch.object(Notebook, "get", new=AsyncMock(return_value=notebook)),
            patch.object(
                Notebook, "get_quizzes", new=AsyncMock(return_value=[quiz])
            ),
        ):
            response = client.get("/api/notebooks/notebook:test/quizzes")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Existing Quiz"

    def test_delete_quiz(self, client):
        quiz = Quiz(id="quiz:1", title="Existing Quiz", questions=[])

        with (
            patch.object(Quiz, "get", new=AsyncMock(return_value=quiz)),
            patch.object(Quiz, "delete", new=AsyncMock(return_value=True)),
        ):
            response = client.delete("/api/quizzes/quiz:1")

        assert response.status_code == 200


class TestFlashcardsRouter:
    """Test suite for the flashcard deck generation/list/get/delete endpoints."""

    def test_generate_deck_empty_notebook_returns_400(self, client):
        notebook = Notebook(id="notebook:test", name="Test", description="Test")

        with (
            patch.object(Notebook, "get", new=AsyncMock(return_value=notebook)),
            patch.object(Notebook, "get_context", new=AsyncMock(return_value="")),
        ):
            response = client.post(
                "/api/notebooks/notebook:test/flashcard-decks",
                json={"num_cards": 5},
            )

        assert response.status_code == 400

    def test_generate_deck_success(self, client):
        notebook = Notebook(id="notebook:test", name="Test", description="Test")

        async def fake_ainvoke(payload, config=None):
            return {"deck": _FakeDeckOutput()}

        async def fake_save(self):
            self.id = "flashcard_deck:new"
            self.created = "2024-01-01T00:00:00"
            self.updated = "2024-01-01T00:00:00"

        with (
            patch.object(Notebook, "get", new=AsyncMock(return_value=notebook)),
            patch.object(
                Notebook, "get_context", new=AsyncMock(return_value="Some content")
            ),
            patch("api.routers.flashcards.flashcards_graph.ainvoke", new=fake_ainvoke),
            patch.object(FlashcardDeck, "save", new=fake_save),
            patch.object(
                FlashcardDeck, "add_to_notebook", new=AsyncMock(return_value=True)
            ),
        ):
            response = client.post(
                "/api/notebooks/notebook:test/flashcard-decks",
                json={"num_cards": 3},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Generated Deck"
        assert len(data["cards"]) == 1
        assert data["cards"][0]["front"] == "RAG"

    def test_delete_deck(self, client):
        deck = FlashcardDeck(id="flashcard_deck:1", title="Existing Deck", cards=[])

        with (
            patch.object(FlashcardDeck, "get", new=AsyncMock(return_value=deck)),
            patch.object(FlashcardDeck, "delete", new=AsyncMock(return_value=True)),
        ):
            response = client.delete("/api/flashcard-decks/flashcard_deck:1")

        assert response.status_code == 200
