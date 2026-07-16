from typing import List

from ai_prompter import Prompter
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.exceptions import OpenNotebookError
from open_notebook.utils import clean_thinking_content
from open_notebook.utils.error_classifier import classify_error
from open_notebook.utils.text_utils import extract_text_content


class FlashcardOutput(BaseModel):
    front: str
    back: str


class FlashcardDeckOutput(BaseModel):
    title: str
    cards: List[FlashcardOutput]


class FlashcardGenerationState(TypedDict):
    context: str
    num_cards: int
    deck: FlashcardDeckOutput


async def generate_flashcards(
    state: FlashcardGenerationState, config: RunnableConfig
) -> dict:
    try:
        parser = PydanticOutputParser(pydantic_object=FlashcardDeckOutput)
        system_prompt = Prompter(
            prompt_template="flashcards/entry", parser=parser
        ).render(data=state)  # type: ignore[arg-type]
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
        deck = parser.parse(cleaned_content)
        return {"deck": deck}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


agent_state = StateGraph(FlashcardGenerationState)
agent_state.add_node("agent", generate_flashcards)  # type: ignore[type-var]
agent_state.add_edge(START, "agent")
agent_state.add_edge("agent", END)

graph = agent_state.compile()
