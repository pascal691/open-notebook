"""
LangGraph workflows for the practice-exam feature.

Two independent single-node graphs:

* ``generate_graph`` — turns a notebook's knowledge into a set of exam
  questions (each with a hidden model answer). An optional reference exam text
  is injected purely as a *style template* so the generated questions match the
  desired format; its content is never used as knowledge.
* ``grade_graph`` — compares a user's answers against the model answers /
  rubric and returns per-question scores plus overall feedback.

Robustness notes
----------------
Both nodes must turn a free-form LLM response into a strict Pydantic object.
Weaker/local models (e.g. small Ollama models) often wrap JSON in prose or code
fences, so we:

* request structured JSON output (``structured={"type": "json"}``) which nudges
  every provider — and forces Ollama's ``format=json`` — toward valid JSON;
* parse defensively (strip code fences, extract the ``{...}`` blob, try the
  Pydantic parser) and retry once with a stronger "JSON only" instruction;
* let the Ollama context window be tuned via ``OPEN_NOTEBOOK_EXAM_NUM_CTX`` so a
  large knowledge base is not silently truncated.
"""

import os
import re
from typing import List, Optional, Type

from ai_prompter import Prompter
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.domain.exam import QuestionType
from open_notebook.exceptions import InvalidInputError, OpenNotebookError
from open_notebook.utils import clean_thinking_content
from open_notebook.utils.error_classifier import classify_error
from open_notebook.utils.text_utils import extract_text_content


# --------------------------------------------------------------------------- #
# Structured output schemas
# --------------------------------------------------------------------------- #
class GeneratedQuestion(BaseModel):
    question: str = Field(description="The question text presented to the student")
    question_type: QuestionType = Field(
        default="open",
        description="One of: multiple_choice, true_false, short_answer, open",
    )
    options: List[str] = Field(
        default_factory=list,
        description="Answer options for multiple_choice/true_false questions; empty otherwise",
    )
    points: int = Field(default=1, description="Maximum points awarded for this question")
    model_answer: str = Field(
        description="The correct/reference answer, used later for grading"
    )
    rubric: Optional[str] = Field(
        default=None, description="Optional guidance on how to award partial credit"
    )


class ExamGeneration(BaseModel):
    questions: List[GeneratedQuestion] = Field(default_factory=list)


class GradedQuestion(BaseModel):
    number: int = Field(description="The question number being graded")
    awarded_points: float = Field(description="Points awarded to the student's answer")
    max_points: float = Field(description="Maximum points for this question")
    correct: bool = Field(
        default=False, description="Whether the answer is essentially correct"
    )
    feedback: str = Field(description="Concise, constructive feedback for the student")


class GradingResult(BaseModel):
    results: List[GradedQuestion] = Field(default_factory=list)
    overall_feedback: str = Field(
        default="", description="Overall assessment and study recommendations"
    )


# --------------------------------------------------------------------------- #
# Robust structured-output helpers
# --------------------------------------------------------------------------- #
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _exam_num_ctx() -> Optional[int]:
    """Optional Ollama context window, configured via OPEN_NOTEBOOK_EXAM_NUM_CTX."""
    raw = os.getenv("OPEN_NOTEBOOK_EXAM_NUM_CTX")
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def _model_call_kwargs(max_tokens: int) -> dict:
    """Kwargs passed to provision_langchain_model for exam generation/grading."""
    kwargs: dict = {"max_tokens": max_tokens, "structured": {"type": "json"}}
    num_ctx = _exam_num_ctx()
    if num_ctx is not None:
        # Only Ollama reads num_ctx; other providers keep it in config and ignore it.
        kwargs["num_ctx"] = num_ctx
    return kwargs


def _coerce_json(content, parser: PydanticOutputParser, cls: Type[BaseModel]):
    """Best-effort parse of a model response into ``cls``; returns None on failure."""
    text = clean_thinking_content(extract_text_content(content))
    candidates: List[str] = []

    fence = _FENCE_RE.search(text)
    if fence:
        candidates.append(fence.group(1))
    # First "{" to last "}" — tolerant of leading/trailing prose.
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        candidates.append(brace.group(0))
    candidates.append(text)

    seen = set()
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            return cls.model_validate_json(candidate)
        except Exception:
            pass
        try:
            return parser.parse(candidate)
        except Exception:
            pass
    return None


async def _run_structured(
    *, template: str, data: dict, cls: Type[BaseModel], model_id, max_tokens: int
):
    """Render a prompt, call the model, and robustly parse a structured result."""
    parser = PydanticOutputParser(pydantic_object=cls)
    system_prompt = Prompter(prompt_template=template, parser=parser).render(data=data)
    model = await provision_langchain_model(
        system_prompt, model_id, "transformation", **_model_call_kwargs(max_tokens)
    )

    for attempt in range(2):
        prompt = system_prompt
        if attempt > 0:
            prompt = (
                system_prompt
                + "\n\nIMPORTANT: your previous answer could not be parsed. Respond "
                "with ONLY the JSON object described above — no prose, no code fences."
            )
        ai_message = await model.ainvoke(prompt)
        parsed = _coerce_json(ai_message.content, parser, cls)
        if parsed is not None:
            return parsed

    raise InvalidInputError(
        "The selected model did not return a valid result in the required JSON "
        "format. Try again, choose a stronger model, or (for Ollama) increase the "
        "context window via OPEN_NOTEBOOK_EXAM_NUM_CTX."
    )


# --------------------------------------------------------------------------- #
# Generation graph
# --------------------------------------------------------------------------- #
class GenerateState(TypedDict, total=False):
    knowledge: str
    reference_text: Optional[str]
    num_questions: int
    difficulty: str
    question_types: List[str]
    language: Optional[str]
    instructions: Optional[str]
    generated: ExamGeneration


async def generate_questions(state: GenerateState, config: RunnableConfig) -> dict:
    try:
        generated = await _run_structured(
            template="exam/generate",
            data=dict(state),
            cls=ExamGeneration,
            model_id=config.get("configurable", {}).get("model_id"),
            max_tokens=8192,
        )
        return {"generated": generated}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


_generate = StateGraph(GenerateState)
_generate.add_node("generate", generate_questions)
_generate.add_edge(START, "generate")
_generate.add_edge("generate", END)
generate_graph = _generate.compile()


# --------------------------------------------------------------------------- #
# Grading graph
# --------------------------------------------------------------------------- #
class GradeState(TypedDict, total=False):
    questions: list  # list of dicts: number, question, question_type, points,
    #                  model_answer, rubric, student_answer
    language: Optional[str]
    graded: GradingResult


async def grade_answers(state: GradeState, config: RunnableConfig) -> dict:
    try:
        graded = await _run_structured(
            template="exam/grade",
            data=dict(state),
            cls=GradingResult,
            model_id=config.get("configurable", {}).get("model_id"),
            max_tokens=8192,
        )
        return {"graded": graded}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


_grade = StateGraph(GradeState)
_grade.add_node("grade", grade_answers)
_grade.add_edge(START, "grade")
_grade.add_edge("grade", END)
grade_graph = _grade.compile()
