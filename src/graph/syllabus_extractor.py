import json
from pathlib import Path

from src.agents.llm_client import get_groq_llm, with_structured_output_retry
from src.graph.concept_graph import ConceptGraph
from src.graph.generate_dataset import ConceptDataset, ConceptDraft, PrerequisiteEdge

SYLLABUS_EXTRACTION_PROMPT = """
Here is a course syllabus:
---
{syllabus_text}
---

Here is the list of concepts ALREADY in our curriculum (id: name):
{existing_concept_list}

Extract the distinct topics/concepts taught in this syllabus, ordered so that
earlier concepts are genuine prerequisites of later ones.

For each concept:
- Give it a new unique snake_case id, UNLESS it is clearly the same concept as
  one already in the curriculum list above — in that case, reuse that EXACT
  existing id and do NOT create a new/duplicate entry for it.
- Assign a domain label matching this syllabus's subject (e.g. "Biology").

Also list prerequisite edges (prerequisite_id -> concept_id). A prerequisite_id
MAY reference either a newly extracted concept OR an id from the existing
curriculum list above, if this syllabus genuinely assumes that prior knowledge.

Rules:
1. The prerequisite edges must form a DAG — no cycles.
2. Only include a prerequisite if it is genuinely required, not just related.
3. Do NOT re-emit a "concepts" entry for any id you are reusing from the
   existing curriculum list — only list truly NEW concepts.
"""


def extract_syllabus_dataset(syllabus_text: str, cg: ConceptGraph) -> ConceptDataset:
    existing_list = "\n".join(
        f"{cid}: {data.get('name') if data is not None else ''}"
        for cid, data in cg.graph.nodes(data=True)
    )
    prompt = SYLLABUS_EXTRACTION_PROMPT.format(syllabus_text=syllabus_text, existing_concept_list=existing_list)

    # reasoning_effort="medium", not "high" — "high" alone needs ~13k tokens on this
    # model for a complex extraction like this, which exceeds this account's 8,000
    # TPM free-tier cap regardless of max_tokens (see generate_dataset.py, which hit
    # this exact wall). max_tokens is capped generously but under that limit.
    llm = get_groq_llm(reasoning_effort="medium", temperature=0.3, max_tokens=6000)
    result = with_structured_output_retry(llm, ConceptDataset, prompt)
    # include_raw=True (the default) returns {"raw", "parsed", "parsing_error"} — unwrap it.
    parsed = result["parsed"] if isinstance(result, dict) else result
    if not isinstance(parsed, ConceptDataset):
        raise TypeError(f"Expected ConceptDataset, got {type(parsed).__name__}")
    return parsed


def merge_dataset(
    existing_dataset_path: str,
    new_concepts: list[ConceptDraft],
    new_edges: list[PrerequisiteEdge],
    output_path: str,
) -> tuple[int, int]:
    """
    Merges newly extracted concepts/edges into the existing dataset file.
    Renames any accidentally colliding concept id (appending its domain) as a
    safety net, and remaps any prerequisite edges that referenced the old id.
    Returns (concepts_added, edges_added).
    """
    existing = json.loads(Path(existing_dataset_path).read_text())
    existing_ids = {c["id"] for c in existing["concepts"]}

    id_remap: dict[str, str] = {}
    deduped_concepts = []
    for c in new_concepts:
        new_id = c.id
        if new_id in existing_ids:
            new_id = f"{c.id}_{c.domain.lower().replace(' ', '_')}"
        id_remap[c.id] = new_id
        deduped_concepts.append({"id": new_id, "name": c.name, "domain": c.domain, "description": c.description})

    remapped_edges = [
        {
            "prerequisite_id": id_remap.get(e.prerequisite_id, e.prerequisite_id),
            "concept_id": id_remap.get(e.concept_id, e.concept_id),
        }
        for e in new_edges
    ]

    existing["concepts"].extend(deduped_concepts)
    existing["prerequisites"].extend(remapped_edges)
    Path(output_path).write_text(json.dumps(existing, indent=2))

    return len(deduped_concepts), len(remapped_edges)