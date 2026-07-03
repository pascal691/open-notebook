"""
Unit tests for the open_notebook.graphs module.

This test suite focuses on testing graph structures, tools, and validation
without heavy mocking of the actual processing logic.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from open_notebook.domain.notebook import Source
from open_notebook.graphs.flashcards import generate_flashcards
from open_notebook.graphs.flashcards import graph as flashcards_graph
from open_notebook.graphs.prompt import PatternChainState, graph
from open_notebook.graphs.quiz import generate_quiz
from open_notebook.graphs.quiz import graph as quiz_graph
from open_notebook.graphs.tools import get_current_timestamp
from open_notebook.graphs.transformation import (
    TransformationState,
    run_transformation,
)
from open_notebook.graphs.transformation import (
    graph as transformation_graph,
)

# ============================================================================
# TEST SUITE 1: Graph Tools
# ============================================================================


class TestGraphTools:
    """Test suite for graph tool definitions."""

    def test_get_current_timestamp_format(self):
        """Test timestamp tool returns correct format."""
        timestamp = get_current_timestamp.func()

        assert isinstance(timestamp, str)
        assert len(timestamp) == 14  # YYYYMMDDHHmmss format
        assert timestamp.isdigit()

    def test_get_current_timestamp_validity(self):
        """Test timestamp represents valid datetime."""
        timestamp = get_current_timestamp.func()

        # Parse it back to datetime to verify validity
        year = int(timestamp[0:4])
        month = int(timestamp[4:6])
        day = int(timestamp[6:8])
        hour = int(timestamp[8:10])
        minute = int(timestamp[10:12])
        second = int(timestamp[12:14])

        # Should be valid date components
        assert 2020 <= year <= 2100
        assert 1 <= month <= 12
        assert 1 <= day <= 31
        assert 0 <= hour <= 23
        assert 0 <= minute <= 59
        assert 0 <= second <= 59

        # Should parse as datetime
        dt = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        assert isinstance(dt, datetime)

    def test_get_current_timestamp_is_tool(self):
        """Test that function is properly decorated as a tool."""
        # Check it has tool attributes
        assert hasattr(get_current_timestamp, "name")
        assert hasattr(get_current_timestamp, "description")


# ============================================================================
# TEST SUITE 2: Prompt Graph State
# ============================================================================


class TestPromptGraph:
    """Test suite for prompt pattern chain graph."""

    def test_pattern_chain_state_structure(self):
        """Test PatternChainState structure and fields."""
        state = PatternChainState(
            prompt="Test prompt", parser=None, input_text="Test input", output=""
        )

        assert state["prompt"] == "Test prompt"
        assert state["parser"] is None
        assert state["input_text"] == "Test input"
        assert state["output"] == ""

    def test_prompt_graph_compilation(self):
        """Test that prompt graph compiles correctly."""
        assert graph is not None

        # Graph should have the expected structure
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "ainvoke")


# ============================================================================
# TEST SUITE 3: Transformation Graph
# ============================================================================


class TestTransformationGraph:
    """Test suite for transformation graph workflows."""

    def test_transformation_state_structure(self):
        """Test TransformationState structure and fields."""
        from unittest.mock import MagicMock

        from open_notebook.domain.notebook import Source
        from open_notebook.domain.transformation import Transformation

        mock_source = MagicMock(spec=Source)
        mock_transformation = MagicMock(spec=Transformation)

        state = TransformationState(
            input_text="Test text",
            source=mock_source,
            transformation=mock_transformation,
            output="",
        )

        assert state["input_text"] == "Test text"
        assert state["source"] == mock_source
        assert state["transformation"] == mock_transformation
        assert state["output"] == ""

    @pytest.mark.asyncio
    async def test_run_transformation_assertion_no_content(self):
        """Test transformation raises assertion with no content."""
        from unittest.mock import MagicMock

        from open_notebook.domain.transformation import Transformation

        mock_transformation = MagicMock(spec=Transformation)

        state = {
            "input_text": None,
            "transformation": mock_transformation,
            "source": None,
        }

        config = {"configurable": {"model_id": None}}

        with pytest.raises(AssertionError, match="No content to transform"):
            await run_transformation(state, config)

    def test_transformation_graph_compilation(self):
        """Test that transformation graph compiles correctly."""
        assert transformation_graph is not None
        assert hasattr(transformation_graph, "invoke")
        assert hasattr(transformation_graph, "ainvoke")


# ============================================================================
# TEST SUITE 3b: Quiz Graph
# ============================================================================


class TestQuizGraph:
    """Test suite for quiz generation graph."""

    def test_quiz_graph_compilation(self):
        """Test that the quiz graph compiles correctly."""
        assert quiz_graph is not None
        assert hasattr(quiz_graph, "invoke")
        assert hasattr(quiz_graph, "ainvoke")

    @pytest.mark.asyncio
    async def test_generate_quiz_parses_structured_output(self):
        """Test generate_quiz calls the tools model and parses the JSON response."""
        quiz_json = (
            '{"title": "Sample Quiz", "questions": [{"question": "Q1?", '
            '"options": ["A", "B", "C", "D"], "correct_answer_index": 2, '
            '"explanation": "Because C."}]}'
        )
        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content=quiz_json))

        state = {"context": "Some notebook content", "num_questions": 1}
        config = {"configurable": {"model_id": None}}

        with patch(
            "open_notebook.graphs.quiz.provision_langchain_model",
            new=AsyncMock(return_value=mock_model),
        ) as mock_provision:
            result = await generate_quiz(state, config)

        assert mock_provision.await_args.kwargs["structured"] == {"type": "json"}
        assert mock_provision.await_args.args[2] == "tools"
        quiz = result["quiz"]
        assert quiz.title == "Sample Quiz"
        assert len(quiz.questions) == 1
        assert quiz.questions[0].correct_answer_index == 2


# ============================================================================
# TEST SUITE 3c: Flashcards Graph
# ============================================================================


class TestFlashcardsGraph:
    """Test suite for flashcard generation graph."""

    def test_flashcards_graph_compilation(self):
        """Test that the flashcards graph compiles correctly."""
        assert flashcards_graph is not None
        assert hasattr(flashcards_graph, "invoke")
        assert hasattr(flashcards_graph, "ainvoke")

    @pytest.mark.asyncio
    async def test_generate_flashcards_parses_structured_output(self):
        """Test generate_flashcards calls the tools model and parses the JSON response."""
        deck_json = (
            '{"title": "Sample Deck", "cards": [{"front": "RAG", '
            '"back": "Retrieval-Augmented Generation"}]}'
        )
        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content=deck_json))

        state = {"context": "Some notebook content", "num_cards": 1}
        config = {"configurable": {"model_id": None}}

        with patch(
            "open_notebook.graphs.flashcards.provision_langchain_model",
            new=AsyncMock(return_value=mock_model),
        ) as mock_provision:
            result = await generate_flashcards(state, config)

        assert mock_provision.await_args.kwargs["structured"] == {"type": "json"}
        assert mock_provision.await_args.args[2] == "tools"
        deck = result["deck"]
        assert deck.title == "Sample Deck"
        assert len(deck.cards) == 1
        assert deck.cards[0].front == "RAG"


# ============================================================================
# TEST SUITE 4: Source Graph - Title Preservation
# ============================================================================


class TestSaveSourceTitlePreservation:
    """Test save_source node preserves user-set titles (#670)."""

    @pytest.mark.asyncio
    @patch("open_notebook.graphs.source.Source.get")
    async def test_custom_title_preserved(self, mock_get):
        """User-set title is NOT overwritten by content_state.title."""
        from open_notebook.graphs.source import save_source

        mock_source = MagicMock(spec=Source)
        mock_source.title = "My Custom Research Title"
        mock_source.save = AsyncMock()
        mock_get.return_value = mock_source

        content_state = MagicMock()
        content_state.title = "video.mp4"
        content_state.url = "https://example.com"
        content_state.file_path = None
        content_state.content = "Some content"

        state = {
            "source_id": "source:123",
            "content_state": content_state,
            "embed": False,
            "apply_transformations": [],
        }

        await save_source(state)

        assert mock_source.title == "My Custom Research Title"
        mock_source.save.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("open_notebook.graphs.source.Source.get")
    async def test_placeholder_title_replaced(self, mock_get):
        """Placeholder 'Processing...' title IS replaced by extracted title."""
        from open_notebook.graphs.source import save_source

        mock_source = MagicMock(spec=Source)
        mock_source.title = "Processing..."
        mock_source.save = AsyncMock()
        mock_get.return_value = mock_source

        content_state = MagicMock()
        content_state.title = "Extracted Article Title"
        content_state.url = "https://example.com"
        content_state.file_path = None
        content_state.content = "Some content"

        state = {
            "source_id": "source:123",
            "content_state": content_state,
            "embed": False,
            "apply_transformations": [],
        }

        await save_source(state)

        assert mock_source.title == "Extracted Article Title"
        mock_source.save.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("open_notebook.graphs.source.Source.get")
    async def test_none_title_replaced(self, mock_get):
        """None title IS replaced by extracted title."""
        from open_notebook.graphs.source import save_source

        mock_source = MagicMock(spec=Source)
        mock_source.title = None
        mock_source.save = AsyncMock()
        mock_get.return_value = mock_source

        content_state = MagicMock()
        content_state.title = "Extracted Title"
        content_state.url = None
        content_state.file_path = "/tmp/file.pdf"
        content_state.content = "Content"

        state = {
            "source_id": "source:123",
            "content_state": content_state,
            "embed": False,
            "apply_transformations": [],
        }

        await save_source(state)

        assert mock_source.title == "Extracted Title"
        mock_source.save.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("open_notebook.graphs.source.Source.get")
    async def test_empty_title_replaced(self, mock_get):
        """Empty string title IS replaced by extracted title."""
        from open_notebook.graphs.source import save_source

        mock_source = MagicMock(spec=Source)
        mock_source.title = ""
        mock_source.save = AsyncMock()
        mock_get.return_value = mock_source

        content_state = MagicMock()
        content_state.title = "Extracted Title"
        content_state.url = None
        content_state.file_path = None
        content_state.content = "Content"

        state = {
            "source_id": "source:123",
            "content_state": content_state,
            "embed": False,
            "apply_transformations": [],
        }

        await save_source(state)

        assert mock_source.title == "Extracted Title"
        mock_source.save.assert_awaited_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
