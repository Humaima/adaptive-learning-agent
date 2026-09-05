from src.graph.concept_graph import ConceptGraph
from src.agents.quiz_generator import generate_quiz
from src.agents.evaluator import evaluate_quiz
from src.models.schemas import DifficultyLevel

cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")
quiz = generate_quiz(cg, concept_id="calculus_derivatives", difficulty=DifficultyLevel.EASY)

print("Quiz questions generated:")
for q in quiz.questions:
    print(f"  [{q.question_id}] ({q.question_type.value}) {q.question_text}")
    if q.options:
        for opt in q.options:
            print(f"      {opt.label}. {opt.text}")

# Simulate answers: get the first question right, second one wrong/vague on purpose
fake_answers = {}
if len(quiz.questions) >= 1:
    q0 = quiz.questions[0]
    fake_answers[q0.question_id] = q0.correct_answer if q0.question_type.value == "mcq" else "I'm not totally sure."
if len(quiz.questions) >= 2:
    q1 = quiz.questions[1]
    fake_answers[q1.question_id] = "A" if q1.question_type.value == "mcq" else "Something vaguely related."

results = evaluate_quiz(quiz.questions, fake_answers)

print("\nEvaluation results:")
for r in results:
    print(r.model_dump_json(indent=2))