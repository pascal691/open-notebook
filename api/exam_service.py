"""
Server-side business logic for the practice-exam feature.

These are in-process async helpers (operating directly on domain models and
LangGraph workflows) used by ``api/routers/exams.py``. They orchestrate:

* assembling a notebook's knowledge into a prompt-sized context,
* generating an exam from that knowledge (with an optional reference exam used
  purely as a style template), and
* grading a user's submission against the questions' model answers.
"""

from typing import Optional

from loguru import logger

from open_notebook.domain.exam import Exam, ExamQuestion, ExamSubmission, QuestionResult
from open_notebook.domain.notebook import Notebook, Source
from open_notebook.exceptions import InvalidInputError
from open_notebook.graphs.exam import generate_graph, grade_graph

# Upper bound on the knowledge context handed to the model. provision_langchain_model
# transparently upgrades to a large-context model above ~105k tokens, but we still cap
# the raw text to keep generation focused and costs predictable (~30k tokens).
MAX_KNOWLEDGE_CHARS = 120_000


async def _build_knowledge(notebook: Notebook) -> str:
    """Assemble the notebook's sources and notes into a single context string."""
    knowledge = await notebook.get_context()
    if not knowledge or not knowledge.strip():
        raise InvalidInputError(
            "This notebook has no content yet. Add sources or notes before "
            "generating an exam."
        )
    if len(knowledge) > MAX_KNOWLEDGE_CHARS:
        logger.info(
            f"Truncating notebook knowledge from {len(knowledge)} to "
            f"{MAX_KNOWLEDGE_CHARS} chars for exam generation"
        )
        knowledge = knowledge[:MAX_KNOWLEDGE_CHARS]
    return knowledge


async def _reference_text(reference_source_id: Optional[str]) -> Optional[str]:
    """Fetch the full text of an uploaded reference exam, if provided."""
    if not reference_source_id:
        return None
    source = await Source.get(reference_source_id)
    text = source.full_text
    if not text or not text.strip():
        logger.warning(
            f"Reference source {reference_source_id} has no extracted text; "
            "ignoring it as a style template."
        )
        return None
    # A style template does not need the whole document; a generous excerpt is plenty.
    return text[:20_000]


async def generate_exam(
    *,
    notebook_id: str,
    title: Optional[str],
    description: Optional[str],
    num_questions: int,
    difficulty: str,
    question_types: list[str],
    language: Optional[str],
    instructions: Optional[str],
    reference_source_id: Optional[str],
    model_id: Optional[str],
) -> Exam:
    """Generate and persist a new exam from a notebook's knowledge."""
    notebook = await Notebook.get(notebook_id)
    knowledge = await _build_knowledge(notebook)
    reference_text = await _reference_text(reference_source_id)

    result = await generate_graph.ainvoke(
        {
            "knowledge": knowledge,
            "reference_text": reference_text,
            "num_questions": num_questions,
            "difficulty": difficulty,
            "question_types": question_types,
            "language": language,
            "instructions": instructions,
        },
        config={"configurable": {"model_id": model_id}},
    )

    generated = result["generated"]
    questions = [
        ExamQuestion(
            number=idx + 1,
            question=q.question,
            question_type=q.question_type,
            options=q.options,
            points=max(1, q.points),
            model_answer=q.model_answer,
            rubric=q.rubric,
        )
        for idx, q in enumerate(generated.questions)
    ]

    if not questions:
        raise InvalidInputError(
            "The model did not return any questions. Try again, optionally with a "
            "different model or fewer question types."
        )

    exam = Exam(
        notebook=notebook_id,
        title=title.strip() if title and title.strip() else f"Practice exam – {notebook.name}",
        description=description,
        num_questions=len(questions),
        difficulty=difficulty,
        question_types=question_types,
        language=language,
        instructions=instructions,
        reference_source=reference_source_id,
        status="ready",
        questions=questions,
    )
    await exam.save()
    # Reload so nested question objects are re-validated from storage.
    return await Exam.get(str(exam.id))


async def grade_submission(
    *, exam: Exam, answers: dict[str, str], model_id: Optional[str]
) -> ExamSubmission:
    """Grade a set of answers against an exam and persist the submission."""
    if not exam.questions:
        raise InvalidInputError("This exam has no questions to grade.")

    questions_payload = [
        {
            "number": q.number,
            "question": q.question,
            "question_type": q.question_type,
            "options": q.options,
            "max_points": q.points,
            "model_answer": q.model_answer,
            "rubric": q.rubric,
            "student_answer": answers.get(str(q.number), "").strip(),
        }
        for q in exam.questions
    ]

    result = await grade_graph.ainvoke(
        {"questions": questions_payload, "language": exam.language},
        config={"configurable": {"model_id": model_id}},
    )
    graded = result["graded"]

    # Index the model's grading by question number so we can align it defensively
    # with the authoritative question list (never trust the model to be exhaustive).
    graded_by_number = {g.number: g for g in graded.results}
    max_by_number = {q.number: q.points for q in exam.questions}

    results: list[QuestionResult] = []
    total_score = 0.0
    max_score = 0.0
    for q in exam.questions:
        max_points = float(q.points)
        max_score += max_points
        g = graded_by_number.get(q.number)
        if g is None:
            results.append(
                QuestionResult(
                    number=q.number,
                    awarded_points=0.0,
                    max_points=max_points,
                    correct=False,
                    feedback="Not graded.",
                )
            )
            continue
        # Clamp awarded points to the valid [0, max_points] range.
        awarded = max(0.0, min(float(g.awarded_points), max_points))
        total_score += awarded
        results.append(
            QuestionResult(
                number=q.number,
                awarded_points=awarded,
                max_points=max_points,
                correct=bool(g.correct),
                feedback=g.feedback,
            )
        )

    percentage = round((total_score / max_score) * 100, 1) if max_score else 0.0

    submission = ExamSubmission(
        exam=str(exam.id),
        answers=answers,
        status="graded",
        graded=True,
        total_score=round(total_score, 2),
        max_score=round(max_score, 2),
        percentage=percentage,
        overall_feedback=graded.overall_feedback,
        results=results,
    )
    await submission.save()
    return await ExamSubmission.get(str(submission.id))
