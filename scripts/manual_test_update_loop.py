from src.db.database import SessionLocal
from src.db.repository import set_mastery
from src.graph.concept_graph import ConceptGraph
from src.agents.assessment import assess_knowledge
from src.agents.difficulty_estimator import estimate_difficulty
from src.agents.tutor import generate_tutoring_content
from src.agents.quiz_generator import generate_quiz
from src.agents.evaluator import evaluate_quiz
from src.agents.update_loop import run_update_loop

db = SessionLocal()
cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")

set_mastery(db, "student_001", "linear_algebra", 0.9)
set_mastery(db, "student_001", "calculus_derivatives", 0.2)  # weak -> triggers redirect

question = "Explain backpropagation."

# --- One full pass: assess -> decide -> teach -> quiz -> grade -> update ---
assessment_result = assess_knowledge(db, "student_001", question, cg)
difficulty_estimate = estimate_difficulty(assessment_result)
print(f"Teaching: {difficulty_estimate.concept_to_teach_next} at {difficulty_estimate.recommended_difficulty.value}")

tutor_response = generate_tutoring_content(cg, assessment_result, difficulty_estimate)
print(f"Transition note: {tutor_response.transition_note}")

quiz = generate_quiz(cg, tutor_response.concept_id, tutor_response.difficulty)
print(f"Generated {len(quiz.questions)} quiz questions.")

# Simulate the student answering EVERY question correctly, to show mastery crossing the threshold
fake_answers = {
    q.question_id: (q.correct_answer if q.question_type.value == "mcq" else q.correct_answer)
    for q in quiz.questions
}
eval_results = evaluate_quiz(quiz.questions, fake_answers)

update_result = run_update_loop(
    db, "student_001", question, assessment_result.target_concept_id, cg, eval_results
)

print("\n--- Update Loop Result ---")
print(update_result.model_dump_json(indent=2))
print(f"\nReady to teach '{assessment_result.target_concept_id}' now? {update_result.ready_to_learn_target_now}")