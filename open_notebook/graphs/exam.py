"""
LangGraph workflows for the practice-exam feature.

Two independent single-node graphs:

* ``generate_graph`` — turns a notebook's knowledge into a set of exam
  questions (each with a hidden model answer). An optional reference exam text
  is injected purely as a *style template* so the generated questions match the
  desired format; its content is never used as knowledge.
* ``grade_graph`` — compares a user's answers against the model answers /
  rubric and returns per-question scores plus overall feedback.

Both nodes follow the repo convention of parsing structured output with a
``PydanticOutputParser`` and stripping extended-thinking tags from the response.
"""

from typing import List, Optional

from ai_prompter import Prompter
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.domain.exam import QuestionType
from open_notebook.exceptions import OpenNotebookError
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
        parser = PydanticOutputParser(pydantic_object=ExamGeneration)
        system_prompt = Prompter(prompt_template="exam/generate", parser=parser).render(
            data=state  # type: ignore[arg-type]
        )
        model = await provision_langchain_model(
            system_prompt,
            config.get("configurable", {}).get("model_id"),
            "transformation",
            max_tokens=8192,
        )
        ai_message = await model.ainvoke(system_prompt)
        content = clean_thinking_content(extract_text_content(ai_message.content))
        generated = parser.parse(content)
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
        parser = PydanticOutputParser(pydantic_object=GradingResult)
        system_prompt = Prompter(prompt_template="exam/grade", parser=parser).render(
            data=state  # type: ignore[arg-type]
        )
        model = await provision_langchain_model(
            system_prompt,
            config.get("configurable", {}).get("model_id"),
            "transformation",
            max_tokens=8192,
        )
        ai_message = await model.ainvoke(system_prompt)
        content = clean_thinking_content(extract_text_content(ai_message.content))
        graded = parser.parse(content)
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
