from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from api.exam_service import generate_exam, grade_submission
from api.models import (
    ExamGenerateRequest,
    ExamListItem,
    ExamQuestionResponse,
    ExamResponse,
    ExamSubmissionResponse,
    ExamSubmitRequest,
    ExamUpdateRequest,
    QuestionResultResponse,
)
from open_notebook.ai.models import Model
from open_notebook.domain.exam import Exam, ExamSubmission
from open_notebook.exceptions import InvalidInputError, NotFoundError, OpenNotebookError

router = APIRouter()


def _question_response(q, include_solutions: bool) -> ExamQuestionResponse:
    return ExamQuestionResponse(
        number=q.number,
        question=q.question,
        question_type=q.question_type,
        options=q.options,
        points=q.points,
        model_answer=q.model_answer if include_solutions else None,
        rubric=q.rubric if include_solutions else None,
    )


def _exam_response(exam: Exam, include_solutions: bool = False) -> ExamResponse:
    return ExamResponse(
        id=str(exam.id or ""),
        notebook_id=str(exam.notebook),
        title=exam.title,
        description=exam.description,
        status=exam.status,
        num_questions=exam.num_questions,
        difficulty=exam.difficulty,
        question_types=exam.question_types,
        language=exam.language,
        instructions=exam.instructions,
        reference_source_id=str(exam.reference_source) if exam.reference_source else None,
        total_points=exam.total_points,
        questions=[_question_response(q, include_solutions) for q in exam.questions],
        created=str(exam.created),
        updated=str(exam.updated),
    )


def _exam_list_item(exam: Exam) -> ExamListItem:
    return ExamListItem(
        id=str(exam.id or ""),
        notebook_id=str(exam.notebook),
        title=exam.title,
        description=exam.description,
        status=exam.status,
        num_questions=exam.num_questions,
        difficulty=exam.difficulty,
        total_points=exam.total_points,
        created=str(exam.created),
        updated=str(exam.updated),
    )


def _submission_response(sub: ExamSubmission) -> ExamSubmissionResponse:
    return ExamSubmissionResponse(
        id=str(sub.id or ""),
        exam_id=str(sub.exam),
        answers=sub.answers,
        status=sub.status,
        graded=sub.graded,
        total_score=sub.total_score,
        max_score=sub.max_score,
        percentage=sub.percentage,
        overall_feedback=sub.overall_feedback,
        results=[
            QuestionResultResponse(
                number=r.number,
                awarded_points=r.awarded_points,
                max_points=r.max_points,
                correct=r.correct,
                feedback=r.feedback,
            )
            for r in sub.results
        ],
        created=str(sub.created),
        updated=str(sub.updated),
    )


async def _validate_model(model_id: Optional[str]) -> None:
    """Reject an unknown model reference up front for a clean error."""
    if model_id:
        model = await Model.get(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")


@router.post("/exams", response_model=ExamResponse)
async def create_exam(request: ExamGenerateRequest):
    """Generate a new practice exam from a notebook's knowledge."""
    try:
        await _validate_model(request.model_id)

        exam = await generate_exam(
            notebook_id=request.notebook_id,
            title=request.title,
            description=request.description,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            question_types=request.question_types,
            language=request.language,
            instructions=request.instructions,
            reference_source_id=request.reference_source_id,
            model_id=request.model_id,
        )
        # The creator sees the exam without solutions (solutions are revealed on grading).
        return _exam_response(exam, include_solutions=False)
    except HTTPException:
        raise
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Notebook or reference source not found")
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OpenNotebookError:
        raise
    except Exception as e:
        logger.error(f"Error generating exam: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating exam: {str(e)}")


@router.get("/exams", response_model=List[ExamListItem])
async def list_exams(
    notebook_id: Optional[str] = Query(None, description="Filter by notebook ID"),
):
    """List exams, optionally filtered by notebook."""
    try:
        if notebook_id:
            exams = await Exam.get_by_notebook(notebook_id)
        else:
            exams = await Exam.get_all(order_by="created desc")
        return [_exam_list_item(exam) for exam in exams]
    except Exception as e:
        logger.error(f"Error listing exams: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing exams: {str(e)}")


@router.get("/exams/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: str,
    include_solutions: bool = Query(
        False, description="Include model answers and rubrics (for review after grading)"
    ),
):
    """Get a specific exam. Model answers are hidden unless explicitly requested."""
    try:
        exam = await Exam.get(exam_id)
        return _exam_response(exam, include_solutions=include_solutions)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Exam not found")
    except Exception as e:
        logger.error(f"Error fetching exam {exam_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching exam: {str(e)}")


@router.put("/exams/{exam_id}", response_model=ExamResponse)
async def update_exam(exam_id: str, update: ExamUpdateRequest):
    """Update an exam's title or description."""
    try:
        exam = await Exam.get(exam_id)
        if update.title is not None:
            exam.title = update.title
        if update.description is not None:
            exam.description = update.description
        await exam.save()
        return _exam_response(await Exam.get(exam_id), include_solutions=False)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Exam not found")
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating exam {exam_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating exam: {str(e)}")


@router.delete("/exams/{exam_id}")
async def delete_exam(exam_id: str):
    """Delete an exam and all of its submissions."""
    try:
        exam = await Exam.get(exam_id)
        await exam.delete()
        return {"message": "Exam deleted successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Exam not found")
    except Exception as e:
        logger.error(f"Error deleting exam {exam_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting exam: {str(e)}")


@router.post("/exams/{exam_id}/submit", response_model=ExamSubmissionResponse)
async def submit_exam(exam_id: str, request: ExamSubmitRequest):
    """Submit answers for an exam and receive an AI-graded result."""
    try:
        await _validate_model(request.model_id)
        exam = await Exam.get(exam_id)
        submission = await grade_submission(
            exam=exam, answers=request.answers, model_id=request.model_id
        )
        return _submission_response(submission)
    except HTTPException:
        raise
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Exam not found")
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OpenNotebookError:
        raise
    except Exception as e:
        logger.error(f"Error grading exam {exam_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error grading exam: {str(e)}")


@router.get("/exams/{exam_id}/submissions", response_model=List[ExamSubmissionResponse])
async def list_submissions(exam_id: str):
    """List all graded submissions for an exam, newest first."""
    try:
        exam = await Exam.get(exam_id)
        submissions = await exam.get_submissions()
        return [_submission_response(sub) for sub in submissions]
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Exam not found")
    except Exception as e:
        logger.error(f"Error listing submissions for exam {exam_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error listing submissions: {str(e)}"
        )


@router.get("/exam-submissions/{submission_id}", response_model=ExamSubmissionResponse)
async def get_submission(submission_id: str):
    """Get a specific exam submission with its grading result."""
    try:
        submission = await ExamSubmission.get(submission_id)
        return _submission_response(submission)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Submission not found")
    except Exception as e:
        logger.error(f"Error fetching submission {submission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching submission: {str(e)}")
