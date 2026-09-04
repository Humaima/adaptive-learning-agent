import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field, SecretStr

load_dotenv()

class ConceptDraft(BaseModel):
    id: str = Field(..., description="Unique lowercase_snake_case identifier, no spaces")
    name: str = Field(..., description="Human-readable concept name")
    domain: str = Field(..., description="Exactly one of: Math, CS, ML, Physics")
    description: str = Field(..., description="One-sentence explanation of the concept")


class PrerequisiteEdge(BaseModel):
    prerequisite_id: str = Field(..., description="id of the concept that must be learned first")
    concept_id: str = Field(..., description="id of the concept that depends on it")

class ConceptDataset(BaseModel):
    concepts: list[ConceptDraft]
    prerequisites: list[PrerequisiteEdge]

GENERATION_PROMPT = """
Design a prerequisite concept graph for an adaptive learning tutor.

Generate 25-30 concepts spanning four domains: Math, CS (Computer Science),
ML (Machine Learning), and Physics.

Rules:
1. Every concept id must be unique snake_case.
2. Prerequisites must form a Directed Acyclic Graph (no cycles, ever).
3. Include real cross-domain prerequisites where pedagogically justified
   (e.g. linear_algebra -> neural_networks, calculus -> backpropagation,
   probability -> statistics, classical_mechanics -> energy_optimization_intuition).
4. Only include a prerequisite if it is genuinely required to understand the concept —
   do not pad the edge list.
5. Aim for roughly 30-40 total prerequisite edges across the whole graph.
"""

def generate_dataset() -> ConceptDataset:
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.3,
        # "high" needs ~13k tokens for this prompt (mostly hidden reasoning), which
        # alone exceeds this account's 8,000 TPM (tokens-per-minute) free-tier cap —
        # a single request that size gets rejected with 413 rate_limit_exceeded no
        # matter what max_tokens is set to. "medium" comfortably fits (~5k tokens)
        # while still giving real reasoning for the dependency structure.
        reasoning_effort="medium",
        reasoning_format="hidden",
        # Without an explicit budget, hidden reasoning can consume the whole
        # completion before any JSON is emitted, leaving empty content and a
        # json_validate_failed error — cap generously but under the TPM limit.
        max_tokens=6000,
        api_key=SecretStr(os.getenv("GROQ_API_KEY") or "")
    )
    structured_llm = llm.with_structured_output(
        ConceptDataset,
        method="json_schema",
        # Non-strict json_schema mode on this model echoes the schema itself
        # before the actual answer (schema JSON + data JSON concatenated with
        # no separator -> invalid JSON -> json_validate_failed). strict=True
        # uses constrained decoding and returns clean data only.
        strict=True,
    )
    result = structured_llm.invoke(GENERATION_PROMPT)
    return ConceptDataset.model_validate(result)  

if __name__ == "__main__":
    dataset = generate_dataset()
    out_path = Path("data/concepts_dataset.json")
    out_path.write_text(dataset.model_dump_json(indent=2), encoding="utf-8")
    print(f"Generated {len(dataset.concepts)} concepts, {len(dataset.prerequisites)} edges.")
    print(f"Saved to {out_path} — open and review before loading into the graph.")