from sqlalchemy.orm import Session

from src.agents.llm_client import get_groq_llm, with_structured_output_retry
from src.graph.concept_graph import ConceptGraph
from src.db.repository import get_mastery
from src.config import MASTERY_THRESHOLD
from src.models.schemas import (
    ConceptIdentification,
    ConceptAssessment,
    MasteryStatus,
    KnowledgeAssessmentResult,
)

IDENTIFICATION_PROMPT_TEMPLATE = """
A student asked the following question:
"{question}"

Here is the list of concepts available in the curriculum (id: name — description):
{concept_list}

Identify which single concept id this question is PRIMARILY about.
Choose only from the ids listed above — do not invent a new id.
"""


def _format_concept_list(cg: ConceptGraph) -> str:
    lines = []
    for node_id, data in cg.graph.nodes(data=True):
        node_data = data or {}
        name = node_data.get("name", "")
        description = node_data.get("description", "")
        lines.append(f"{node_id}: {name} — {description}")
    return "\n".join(lines)


def identify_target_concept(question: str, cg: ConceptGraph) -> ConceptIdentification:
    llm = get_groq_llm(reasoning_effort="medium")
    prompt = IDENTIFICATION_PROMPT_TEMPLATE.format(
        question=question,
        concept_list=_format_concept_list(cg),
    )
    result = with_structured_output_retry(llm, ConceptIdentification, prompt)
    if isinstance(result, dict):
        identification = result["parsed"]
    else:
        identification = getattr(result, "parsed")

    # Safety check: LLMs occasionally drift from the provided list despite instructions.
    if identification.target_concept_id not in cg.graph.nodes:
        raise ValueError(
            f"LLM returned unknown concept id '{identification.target_concept_id}' "
            f"— not present in the concept graph."
        )
    return identification


def mastery_to_status(mastery: float | None) -> MasteryStatus:
    if mastery is None:
        return MasteryStatus.UNKNOWN
    if mastery >= MASTERY_THRESHOLD:
        return MasteryStatus.MASTERED
    return MasteryStatus.NOT_MASTERED


def assess_knowledge(
    db: Session, student_id: str, question: str, cg: ConceptGraph
) -> KnowledgeAssessmentResult:
    identification = identify_target_concept(question, cg)
    target_id = identification.target_concept_id

    learning_path = cg.get_learning_path(target_id)  # prerequisites (ordered) + target

    assessments = []
    for concept_id in learning_path:
        mastery = get_mastery(db, student_id, concept_id)
        status = mastery_to_status(mastery)
        assessments.append(ConceptAssessment(concept_id=concept_id, status=status, mastery=mastery))

    return KnowledgeAssessmentResult(
        student_id=student_id,
        original_question=question,
        target_concept_id=target_id,
        learning_path=learning_path,
        assessments=assessments,
    )