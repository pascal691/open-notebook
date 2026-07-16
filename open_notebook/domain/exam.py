"""
Domain models for the practice-exam feature.

An :class:`Exam` is a set of AI-generated questions grounded in the knowledge of
a notebook (its sources and notes). An uploaded reference exam can be used purely
as a *style template* so the generated questions match the look and feel the user
expects. An :class:`ExamSubmission` records a user's answers together with the
AI grading result.
"""

from typing import Any, ClassVar, Dict, List, Literal, Optional, Union

from loguru import logger
from pydantic import BaseModel, Field, field_validator
from surrealdb import RecordID

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.base import ObjectModel
from open_notebook.exceptions import DatabaseOperationError, InvalidInputError

QuestionType = Literal["multiple_choice", "true_false", "short_answer", "open"]
Difficulty = Literal["easy", "medium", "hard", "mixed"]


class ExamQuestion(BaseModel):
    """A single exam question with its (hidden) model answer and grading rubric."""

    number: int
    question: str
    question_type: QuestionType = "open"
    # Answer options, only relevant for multiple_choice / true_false questions.
    options: List[str] = Field(default_factory=list)
    points: int = 1
    # The reference solution. Never shown while the exam is being taken; only
    # revealed once a submission has been graded.
    model_answer: str = ""
    # Optional guidance for the grader on how to award partial credit.
    rubric: Optional[str] = None


class QuestionResult(BaseModel):
    """Grading outcome for one question."""

    number: int
    awarded_points: float
    max_points: float
    correct: bool = False
    feedback: str = ""


class Exam(ObjectModel):
    table_name: ClassVar[str] = "exam"
    nullable_fields: ClassVar[set[str]] = {"description", "reference_source", "instructions"}

    notebook: Union[str, RecordID]
    title: str
    description: Optional[str] = None
    # Generation parameters, kept so an exam can be regenerated / audited.
    num_questions: int = 5
    difficulty: Difficulty = "medium"
    question_types: List[QuestionType] = Field(default_factory=lambda: ["open"])
    language: Optional[str] = None
    instructions: Optional[str] = None
    # Optional reference exam used only as a formatting/style template.
    reference_source: Optional[Union[str, RecordID]] = None
    status: Literal["generating", "ready", "failed"] = "ready"
    questions: List[ExamQuestion] = Field(default_factory=list)

    @field_validator("id", "notebook", "reference_source", mode="before")
    @classmethod
    def _stringify_record_ids(cls, value):
        """Coerce RecordID values coming back from SurrealDB into strings."""
        if value is None:
            return None
        if isinstance(value, RecordID):
            return str(value)
        return str(value) if value else None

    @field_validator("title")
    @classmethod
    def _title_not_empty(cls, v):
        if not v or not v.strip():
            raise InvalidInputError("Exam title cannot be empty")
        return v

    def _prepare_save_data(self) -> Dict[str, Any]:
        data = super()._prepare_save_data()
        if data.get("notebook") is not None:
            data["notebook"] = ensure_record_id(data["notebook"])
        if data.get("reference_source") is not None:
            data["reference_source"] = ensure_record_id(data["reference_source"])
        return data

    @property
    def total_points(self) -> int:
        return sum(q.points for q in self.questions)

    @classmethod
    async def get_by_notebook(cls, notebook_id: str) -> List["Exam"]:
        """Return all exams that belong to a notebook, newest first."""
        if not notebook_id:
            raise InvalidInputError("Notebook ID must be provided")
        try:
            result = await repo_query(
                "SELECT * FROM exam WHERE notebook = $notebook ORDER BY created DESC",
                {"notebook": ensure_record_id(notebook_id)},
            )
            return [cls(**row) for row in result]
        except Exception as e:
            logger.error(f"Error fetching exams for notebook {notebook_id}: {str(e)}")
            logger.exception(e)
            raise DatabaseOperationError(e)

    async def get_submissions(self) -> List["ExamSubmission"]:
        """Return all submissions for this exam, newest first."""
        try:
            result = await repo_query(
                "SELECT * FROM exam_submission WHERE exam = $exam ORDER BY created DESC",
                {"exam": ensure_record_id(self.id)},
            )
            return [ExamSubmission(**row) for row in result]
        except Exception as e:
            logger.error(f"Error fetching submissions for exam {self.id}: {str(e)}")
            logger.exception(e)
            raise DatabaseOperationError(e)

    async def delete(self) -> bool:
        """Delete the exam and cascade-delete its submissions."""
        try:
            await repo_query(
                "DELETE exam_submission WHERE exam = $exam",
                {"exam": ensure_record_id(self.id)},
            )
        except Exception as e:
            logger.warning(
                f"Failed to delete submissions for exam {self.id}: {e}. "
                "Continuing with exam deletion."
            )
        return await super().delete()


class ExamSubmission(ObjectModel):
    table_name: ClassVar[str] = "exam_submission"

    exam: Union[str, RecordID]
    # Maps question number -> the user's answer text.
    answers: Dict[str, str] = Field(default_factory=dict)
    status: Literal["submitted", "graded", "failed"] = "submitted"
    graded: bool = False
    total_score: float = 0.0
    max_score: float = 0.0
    percentage: float = 0.0
    overall_feedback: str = ""
    results: List[QuestionResult] = Field(default_factory=list)

    @field_validator("id", "exam", mode="before")
    @classmethod
    def _stringify_record_ids(cls, value):
        if value is None:
            return None
        if isinstance(value, RecordID):
            return str(value)
        return str(value) if value else None

    def _prepare_save_data(self) -> Dict[str, Any]:
        data = super()._prepare_save_data()
        if data.get("exam") is not None:
            data["exam"] = ensure_record_id(data["exam"])
        return data

    async def get_exam(self) -> "Exam":
        return await Exam.get(str(self.exam))
