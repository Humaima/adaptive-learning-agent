from pydantic import BaseModel, Field

from src.agents.llm_client import get_groq_llm, with_structured_output_retry
from src.graph.concept_graph import ConceptGraph
from src.config import NUM_FLASHCARDS_PER_CONCEPT


class FlashcardDraft(BaseModel):
    front: str = Field(..., description="A short question or prompt testing recall of one fact/idea")
    back: str = Field(..., description="A concise answer, 1-2 sentences max")


class FlashcardSetDraft(BaseModel):
    cards: list[FlashcardDraft]


FLASHCARD_PROMPT_TEMPLATE = """
Create {num_cards} flashcards to help a student memorize key facts about:

Concept: {concept_name}
Description: {concept_description}

Each front should be short and specific. Each back should be concise —
flashcards are for quick recall, not full explanations.
"""


def generate_flashcards(cg: ConceptGraph, concept_id: str, num_cards: int = NUM_FLASHCARDS_PER_CONCEPT) -> list[tuple[str, str]]:
    info = cg.get_concept_info(concept_id)
    prompt = FLASHCARD_PROMPT_TEMPLATE.format(
        concept_name=info["name"], concept_description=info["description"], num_cards=num_cards
    )
    llm = get_groq_llm(reasoning_effort="low", temperature=0.4)  # short recall facts don't need heavy reasoning
    result = with_structured_output_retry(llm, FlashcardSetDraft, prompt)
    # include_raw=True (the default) returns {"raw", "parsed", "parsing_error"} — unwrap it.
    parsed = result["parsed"] if isinstance(result, dict) else result
    if not isinstance(parsed, FlashcardSetDraft):
        raise TypeError(f"Expected FlashcardSetDraft, got {type(parsed).__name__}")
    return [(c.front, c.back) for c in parsed.cards]