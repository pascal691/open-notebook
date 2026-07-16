from typing import List

from ai_prompter import Prompter
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.exceptions import OpenNotebookError
from open_notebook.utils import clean_thinking_content
from open_notebook.utils.error_classifier import classify_error
from open_notebook.utils.text_utils import extract_text_content


class QuizQuestionOutput(BaseModel):
    question: str
    options: List[str] = Field(..., description="Exactly 4 answer options")
    correct_answer_index: int = Field(
        ..., description="0-based index of the correct option"
    )
    explanation: str = Field(..., description="Why this answer is correct")


class QuizOutput(BaseModel):
    title: str
    questions: List[QuizQuestionOutput]


class QuizGenerationState(TypedDict):
    context: str
    num_questions: int
    quiz: QuizOutput


async def generate_quiz(state: QuizGenerationState, config: RunnableConfig) -> dict:
    try:
        parser = PydanticOutputParser(pydantic_object=QuizOutput)
        system_prompt = Prompter(prompt_template="quiz/entry", parser=parser).render(  # type: ignore[arg-type]
            data=state  # type: ignore[arg-type]
        )
        model = await provision_langchain_model(
            system_prompt,
            config.get("configurable", {}).get("model_id"),
            "tools",
            max_tokens=4000,
            structured=dict(type="json"),
        )
        ai_message = await model.ainvoke(system_prompt)
        message_content = extract_text_content(ai_message.content)
        cleaned_content = clean_thinking_content(message_content)
        quiz = parser.parse(cleaned_content)
        return {"quiz": quiz}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


agent_state = StateGraph(QuizGenerationState)
agent_state.add_node("agent", generate_quiz)  # type: ignore[type-var]
agent_state.add_edge(START, "agent")
agent_state.add_edge("agent", END)

graph = agent_state.compile()
