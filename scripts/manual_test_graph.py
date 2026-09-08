from langgraph.types import Command
from langchain_core.runnables import RunnableConfig

from src.db.database import SessionLocal
from src.db.repository import set_mastery
from src.graph.concept_graph import ConceptGraph
from src.agents.tutor_graph import build_tutor_graph

db = SessionLocal()
cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")

set_mastery(db, "student_001", "linear_algebra", 0.9)
set_mastery(db, "student_001", "calculus", 0.2)  # weak -> expect a redirect + looping

graph = build_tutor_graph(cg)

# Every run needs a thread_id — this is how the checkpointer knows which
# paused conversation to resume later. Use the same one throughout this session.
config: RunnableConfig = {"configurable": {"thread_id": "demo-session-1"}}

# --- Kick off the graph. It will run until it hits the interrupt in collect_answers_node. ---
result = graph.invoke(
    {"student_id": "student_001", "original_question": "Explain backpropagation."},
    config=config,
)

# Keep resuming with answers until the graph reports no more interrupts (i.e. it's truly done).
while "__interrupt__" in result:
    quiz_payload = result["__interrupt__"][0].value
    print(f"\n--- Quiz on: {quiz_payload['concept_id']} (difficulty: {quiz_payload['difficulty']}) ---")

    fake_answers = {}
    for q in quiz_payload["questions"]:
        print(f"  [{q['question_id']}] ({q['question_type']}) {q['question_text']}")
        for opt in q["options"]:
            print(f"      {opt['label']}. {opt['text']}")
        # Simulate a student answering — in a real app this comes from the UI/API instead.
        fake_answers[q["question_id"]] = q["options"][-1]["label"] if q["options"] else "a reasonable guess"

    result = graph.invoke(Command(resume=fake_answers), config=config)

print("\n--- DONE ---")
print("Teaching history (concepts covered this session, in order):")
for tr in result["teaching_history"]:
    print(f"  - {tr.concept_name} (difficulty: {tr.difficulty.value}, redirect: {tr.is_prerequisite_redirect})")