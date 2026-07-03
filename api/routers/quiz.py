from typing import List

from fastapi import APIRouter, HTTPException
from loguru import logger

from api.models import QuizGenerateRequest, QuizQuestionResponse, QuizResponse
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.quiz import Quiz
from open_notebook.exceptions import OpenNotebookError
from open_notebook.graphs.quiz import graph as quiz_graph

router = APIRouter()


def _quiz_response(quiz: Quiz) -> QuizResponse:
    return QuizResponse(
        id=quiz.id or "",
        title=quiz.title,
        questions=[QuizQuestionResponse(**q) for q in quiz.questions],
        created=str(quiz.created),
        updated=str(quiz.updated),
    )


@router.post("/notebooks/{notebook_id}/quizzes", response_model=QuizResponse)
async def generate_quiz(notebook_id: str, request: QuizGenerateRequest):
    """Generate a new multiple-choice quiz from a notebook's content."""
    try:
        notebook = await Notebook.get(notebook_id)

        context = await notebook.get_context()
        if not context.strip():
            raise HTTPException(
                status_code=400,
                detail="This notebook has no content yet. Add sources or notes first.",
            )

        result = await quiz_graph.ainvoke(
            dict(context=context, num_questions=request.num_questions),  # type: ignore[arg-type]
            config=dict(configurable={"model_id": request.model_id}),
        )
        quiz_output = result["quiz"]

        quiz = Quiz(
            title=quiz_output.title,
            questions=[q.model_dump() for q in quiz_output.questions],
        )
        await quiz.save()
        await quiz.add_to_notebook(notebook_id)

        return _quiz_response(quiz)
    except HTTPException:
        raise
    except OpenNotebookError:
        raise
    except Exception as e:
        logger.error(f"Error generating quiz for notebook {notebook_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")


@router.get("/notebooks/{notebook_id}/quizzes", response_model=List[QuizResponse])
async def list_quizzes(notebook_id: str):
    """List all quizzes generated for a notebook."""
    try:
        notebook = await Notebook.get(notebook_id)
        quizzes = await notebook.get_quizzes()
        return [_quiz_response(quiz) for quiz in quizzes]
    except HTTPException:
        raise
    except OpenNotebookError:
        raise
    except Exception as e:
        logger.error(f"Error listing quizzes for notebook {notebook_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list quizzes: {str(e)}")


@router.get("/quizzes/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: str):
    """Get a single quiz by ID."""
    try:
        quiz = await Quiz.get(quiz_id)
        return _quiz_response(quiz)
    except HTTPException:
        raise
    except OpenNotebookError:
        raise
    except Exception as e:
        logger.error(f"Error fetching quiz {quiz_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch quiz: {str(e)}")


@router.delete("/quizzes/{quiz_id}")
async def delete_quiz(quiz_id: str):
    """Delete a quiz."""
    try:
        quiz = await Quiz.get(quiz_id)
        await quiz.delete()
        return {"message": "Quiz deleted successfully"}
    except HTTPException:
        raise
    except OpenNotebookError:
        raise
    except Exception as e:
        logger.error(f"Error deleting quiz {quiz_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete quiz: {str(e)}")
