from typing import cast

from src.agents.llm_client import get_groq_llm, with_structured_output_retry
from src.graph.concept_graph import ConceptGraph
from src.models.schemas import (
    KnowledgeAssessmentResult,
    DifficultyEstimate,
    DifficultyLevel,
    TutorContentDraft,
    TutorResponse,
)

# Plain-language instructions per difficulty band — this is what actually
# changes the LLM's teaching style, not just the topic.
DIFFICULTY_INSTRUCTIONS = {
    DifficultyLevel.EASY: (
        "Explain this as if to someone encountering it for the very first time. "
        "Use simple everyday language, avoid jargon (or define it immediately when used), "
        "and lean on an intuitive analogy before any technical detail."
    ),
    DifficultyLevel.MEDIUM: (
        "Explain this assuming the student has basic familiarity with the prerequisites "
        "but hasn't mastered this specific concept. Use standard technical terms, "
        "but still explain the 'why', not just the 'what'."
    ),
    DifficultyLevel.HARD: (
        "Explain this at a level that challenges someone who already grasps the basics. "
        "Go into more depth, mention an edge case or common misconception, "
        "and connect it to related advanced ideas where relevant."
    ),
}

TEACHING_PROMPT_TEMPLATE = """
You are tutoring a student. Teach them the concept below.

Concept: {concept_name}
Description: {concept_description}

Difficulty instructions: {difficulty_instruction}

{redirect_context}

Produce:
1. A clear explanation matched to the difficulty instructions above.
2. 3-5 short key-point takeaways.
3. One concrete worked example.
4. A transition_note ONLY if redirect context above is present — otherwise leave it as an empty string.
"""

REDIRECT_CONTEXT_TEMPLATE = """
IMPORTANT CONTEXT: The student actually asked about "{target_concept_name}", but they haven't yet
mastered "{current_concept_name}", which is a required building block for it. You are teaching
"{current_concept_name}" FIRST. Write a one-sentence transition_note explaining this to the student
in an encouraging, non-discouraging way (e.g. "Before we get to X, let's make sure Y is solid, since X builds directly on it.").
"""


def _build_prompt(cg: ConceptGraph, concept_id: str, difficulty: DifficultyLevel,
                   is_redirect: bool, target_concept_id: str) -> str:
    concept_info = cg.get_concept_info(concept_id)

    redirect_context = ""
    if is_redirect:
        target_info = cg.get_concept_info(target_concept_id)
        redirect_context = REDIRECT_CONTEXT_TEMPLATE.format(
            target_concept_name=target_info["name"],
            current_concept_name=concept_info["name"],
        )

    return TEACHING_PROMPT_TEMPLATE.format(
        concept_name=concept_info["name"],
        concept_description=concept_info["description"],
        difficulty_instruction=DIFFICULTY_INSTRUCTIONS[difficulty],
        redirect_context=redirect_context,
    )


def generate_tutoring_content(
    cg: ConceptGraph,
    assessment_result: KnowledgeAssessmentResult,
    difficulty_estimate: DifficultyEstimate,
) -> TutorResponse:
    concept_id = difficulty_estimate.concept_to_teach_next
    target_id = assessment_result.target_concept_id
    is_redirect = concept_id != target_id

    concept_info = cg.get_concept_info(concept_id)
    prompt = _build_prompt(
        cg, concept_id, difficulty_estimate.recommended_difficulty, is_redirect, target_id
    )

    # Higher reasoning effort here than Phase 3's identification call — generating a
    # genuinely good explanation benefits more from extra thinking than a one-word classification does.
    llm = get_groq_llm(reasoning_effort="medium", temperature=0.4)
    result = with_structured_output_retry(llm, TutorContentDraft, prompt)
    # include_raw=True (the default) returns {"raw", "parsed", "parsing_error"} — unwrap it.
    draft = cast(TutorContentDraft, result["parsed"] if isinstance(result, dict) else result)

    return TutorResponse(
        concept_id=concept_id,
        concept_name=concept_info["name"],
        difficulty=difficulty_estimate.recommended_difficulty,
        is_prerequisite_redirect=is_redirect,
        target_concept_id=target_id,
        original_question=assessment_result.original_question,
        explanation=draft.explanation,
        key_points=draft.key_points,
        worked_example=draft.worked_example,
        transition_note=draft.transition_note,
    )