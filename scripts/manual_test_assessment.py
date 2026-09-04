from src.db.database import SessionLocal
from src.db.repository import set_mastery
from src.graph.concept_graph import ConceptGraph
from src.agents.assessment import assess_knowledge

db = SessionLocal()
cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")

# Simulate a student who knows linear algebra but not calculus (matches your original example)
set_mastery(db, "student_001", "linear_algebra", 0.9)
set_mastery(db, "student_001", "calculus", 0.2)
# neural_networks and backpropagation left unassessed -> should come back UNKNOWN

result = assess_knowledge(db, "student_001", "Explain backpropagation.", cg)
print(result.model_dump_json(indent=2))