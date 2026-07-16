"""
Unit tests for the practice-exam feature: domain models, graph structure, and
the generation/grading service orchestration (with graphs and DB mocked out).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from surrealdb import RecordID

from open_notebook.domain.exam import (
    Exam,
    ExamQuestion,
    ExamSubmission,
    QuestionResult,
)
from open_notebook.exceptions import InvalidInputError
from open_notebook.graphs.exam import (
    ExamGeneration,
    GeneratedQuestion,
    GradedQuestion,
    GradingResult,
    _coerce_json,
    _exam_num_ctx,
    _model_call_kwargs,
    _run_structured,
    generate_graph,
    grade_graph,
)


# ============================================================================
# Domain models
# ============================================================================
class TestExamDomain:
    def test_title_must_not_be_empty(self):
        with pytest.raises(InvalidInputError):
            Exam(notebook="notebook:1", title="   ")

    def test_record_id_fields_coerced_to_str(self):
        exam = Exam(
            notebook=RecordID("notebook", "abc"),
            title="T",
            reference_source=RecordID("source", "xyz"),
        )
        assert exam.notebook == "notebook:abc"
        assert isinstance(exam.notebook, str)
        assert exam.reference_source == "source:xyz"

    def test_total_points(self):
        exam = Exam(
            notebook="notebook:1",
            title="T",
            questions=[
                ExamQuestion(number=1, question="q1", points=2, model_answer="a"),
                ExamQuestion(number=2, question="q2", points=3, model_answer="b"),
            ],
        )
        assert exam.total_points == 5

    def test_prepare_save_converts_records(self):
        exam = Exam(
            notebook="notebook:1",
            title="T",
            reference_source="source:2",
            questions=[ExamQuestion(number=1, question="q", model_answer="a")],
        )
        data = exam._prepare_save_data()
        assert isinstance(data["notebook"], RecordID)
        assert isinstance(data["reference_source"], RecordID)
        # Questions serialize to plain dicts for SurrealDB
        assert isinstance(data["questions"], list)
        assert data["questions"][0]["number"] == 1

    def test_question_type_default(self):
        q = ExamQuestion(number=1, question="q", model_answer="a")
        assert q.question_type == "open"
        assert q.options == []

    def test_submission_defaults(self):
        sub = ExamSubmission(exam="exam:1", answers={"1": "x"})
        assert sub.graded is False
        assert sub.status == "submitted"
        assert sub.total_score == 0.0


# ============================================================================
# Graph structure
# ============================================================================
class TestExamGraphs:
    def test_graphs_compiled(self):
        assert hasattr(generate_graph, "ainvoke")
        assert hasattr(grade_graph, "ainvoke")

    def test_generation_schema(self):
        gen = ExamGeneration(
            questions=[
                GeneratedQuestion(question="q", model_answer="a", points=2),
            ]
        )
        assert gen.questions[0].question_type == "open"

    def test_grading_schema(self):
        result = GradingResult(
            results=[
                GradedQuestion(
                    number=1, awarded_points=1.0, max_points=2.0, correct=False,
                    feedback="ok",
                )
            ],
            overall_feedback="good",
        )
        assert result.results[0].number == 1


# ============================================================================
# Generation service
# ============================================================================
@pytest.mark.asyncio
async def test_generate_exam_numbers_and_persists():
    notebook = MagicMock()
    notebook.name = "Biology"
    notebook.get_context = AsyncMock(return_value="Cells are the unit of life.")

    generated = ExamGeneration(
        questions=[
            GeneratedQuestion(question="What is a cell?", model_answer="unit of life", points=0),
            GeneratedQuestion(question="Define mitosis", model_answer="cell division", points=3),
        ]
    )

    saved_holder = {}

    async def fake_save(self):
        self.id = "exam:generated"
        saved_holder["exam"] = self

    async def fake_get(cls, exam_id):
        return saved_holder["exam"]

    from api import exam_service

    with patch.object(exam_service, "Notebook") as MockNotebook, patch.object(
        exam_service.generate_graph, "ainvoke", AsyncMock(return_value={"generated": generated})
    ), patch.object(Exam, "save", fake_save), patch.object(
        Exam, "get", classmethod(fake_get)
    ):
        MockNotebook.get = AsyncMock(return_value=notebook)

        exam = await exam_service.generate_exam(
            notebook_id="notebook:1",
            title=None,
            description=None,
            num_questions=2,
            difficulty="medium",
            question_types=["open"],
            language=None,
            instructions=None,
            reference_source_id=None,
            model_id=None,
        )

    saved = saved_holder["exam"]
    # Questions are renumbered 1..n and points floored to >= 1
    assert [q.number for q in saved.questions] == [1, 2]
    assert saved.questions[0].points == 1  # 0 -> 1
    assert saved.questions[1].points == 3
    # Title auto-generated from notebook name
    assert "Biology" in saved.title
    assert exam is saved


@pytest.mark.asyncio
async def test_generate_exam_rejects_empty_notebook():
    notebook = MagicMock()
    notebook.get_context = AsyncMock(return_value="   ")

    from api import exam_service

    with patch.object(exam_service, "Notebook") as MockNotebook:
        MockNotebook.get = AsyncMock(return_value=notebook)
        with pytest.raises(InvalidInputError):
            await exam_service.generate_exam(
                notebook_id="notebook:1",
                title=None,
                description=None,
                num_questions=2,
                difficulty="medium",
                question_types=["open"],
                language=None,
                instructions=None,
                reference_source_id=None,
                model_id=None,
            )


# ============================================================================
# Grading service
# ============================================================================
@pytest.mark.asyncio
async def test_grade_submission_clamps_and_scores():
    exam = Exam(
        id="exam:1",
        notebook="notebook:1",
        title="T",
        language="German",
        questions=[
            ExamQuestion(number=1, question="q1", points=2, model_answer="a"),
            ExamQuestion(number=2, question="q2", points=4, model_answer="b"),
        ],
    )

    # Model over-awards Q1 (should clamp to 2) and omits Q2 entirely.
    graded = GradingResult(
        results=[
            GradedQuestion(number=1, awarded_points=99.0, max_points=2.0, correct=True, feedback="great"),
        ],
        overall_feedback="solid",
    )

    saved_holder = {}

    async def fake_save(self):
        self.id = "exam_submission:1"
        saved_holder["sub"] = self

    async def fake_get(cls, sub_id):
        return saved_holder["sub"]

    from api import exam_service

    with patch.object(
        exam_service.grade_graph, "ainvoke", AsyncMock(return_value={"graded": graded})
    ), patch.object(ExamSubmission, "save", fake_save), patch.object(
        ExamSubmission, "get", classmethod(fake_get)
    ):
        submission = await exam_service.grade_submission(
            exam=exam, answers={"1": "a", "2": "wrong"}, model_id=None
        )

    sub = saved_holder["sub"]
    assert sub.max_score == 6.0
    # Q1 clamped to 2, Q2 defaulted to 0 (not graded)
    assert sub.total_score == 2.0
    assert sub.percentage == round(2.0 / 6.0 * 100, 1)
    q2_result = next(r for r in sub.results if r.number == 2)
    assert q2_result.awarded_points == 0.0
    assert q2_result.max_points == 4.0
    assert sub.graded is True
    assert submission is sub


@pytest.mark.asyncio
async def test_grade_submission_requires_questions():
    exam = Exam(id="exam:1", notebook="notebook:1", title="T", questions=[])
    from api import exam_service

    with pytest.raises(InvalidInputError):
        await exam_service.grade_submission(exam=exam, answers={}, model_id=None)


# ============================================================================
# Robust structured-output parsing
# ============================================================================
class TestRobustParsing:
    parser = PydanticOutputParser(pydantic_object=ExamGeneration)

    def test_clean_json(self):
        c = '{"questions":[{"question":"Q","model_answer":"A","points":2}]}'
        r = _coerce_json(c, self.parser, ExamGeneration)
        assert r and r.questions[0].points == 2

    def test_json_in_code_fence_with_prose(self):
        c = 'Sure!\n```json\n{"questions":[{"question":"Q2","model_answer":"A2"}]}\n```\nDone'
        r = _coerce_json(c, self.parser, ExamGeneration)
        assert r and r.questions[0].question == "Q2"

    def test_json_with_thinking_tags_and_trailing_prose(self):
        c = '<think>plan</think> {"questions":[{"question":"Q3","model_answer":"A3"}]} ok'
        r = _coerce_json(c, self.parser, ExamGeneration)
        assert r and r.questions[0].question == "Q3"

    def test_unparseable_returns_none(self):
        assert _coerce_json("I cannot do that", self.parser, ExamGeneration) is None

    def test_model_call_kwargs_defaults(self, monkeypatch):
        monkeypatch.delenv("OPEN_NOTEBOOK_EXAM_NUM_CTX", raising=False)
        k = _model_call_kwargs(8192)
        assert k["max_tokens"] == 8192
        assert k["structured"] == {"type": "json"}
        assert "num_ctx" not in k

    def test_num_ctx_env(self, monkeypatch):
        monkeypatch.setenv("OPEN_NOTEBOOK_EXAM_NUM_CTX", "16384")
        assert _exam_num_ctx() == 16384
        assert _model_call_kwargs(1)["num_ctx"] == 16384
        monkeypatch.setenv("OPEN_NOTEBOOK_EXAM_NUM_CTX", "notanint")
        assert _exam_num_ctx() is None


class _FakeModel:
    """Async model stub returning canned responses per ainvoke call."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    async def ainvoke(self, prompt):
        idx = min(self.calls, len(self.responses) - 1)
        self.calls += 1
        return type("Msg", (), {"content": self.responses[idx]})()


@pytest.mark.asyncio
async def test_run_structured_retries_then_succeeds():
    fake = _FakeModel([
        "sorry, I can't",  # first attempt: garbage
        '{"questions":[{"question":"Q","model_answer":"A"}]}',  # retry: valid
    ])
    from open_notebook.graphs import exam as exam_graph

    with patch.object(exam_graph, "provision_langchain_model", AsyncMock(return_value=fake)):
        result = await _run_structured(
            template="exam/generate",
            data={"knowledge": "k", "num_questions": 1, "difficulty": "easy",
                  "question_types": ["open"]},
            cls=ExamGeneration,
            model_id=None,
            max_tokens=100,
        )
    assert result.questions[0].question == "Q"
    assert fake.calls == 2  # retried once


@pytest.mark.asyncio
async def test_run_structured_raises_on_persistent_garbage():
    fake = _FakeModel(["nope", "still nope"])
    from open_notebook.graphs import exam as exam_graph

    with patch.object(exam_graph, "provision_langchain_model", AsyncMock(return_value=fake)):
        with pytest.raises(InvalidInputError):
            await _run_structured(
                template="exam/grade",
                data={"questions": [], "language": None},
                cls=GradingResult,
                model_id=None,
                max_tokens=100,
            )
