from src.graph.concept_graph import ConceptGraph
from src.agents.quiz_generator import generate_quiz
from src.models.schemas import DifficultyLevel

cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")

quiz = generate_quiz(cg, concept_id="calculus_derivatives", difficulty=DifficultyLevel.EASY)
print(quiz.model_dump_json(indent=2))