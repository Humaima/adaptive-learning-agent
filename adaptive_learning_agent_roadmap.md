# Adaptive Learning Agent — Implementation Roadmap

## 1. Scope Recap
An AI tutor that doesn't just answer questions — it diagnoses *what the student doesn't know*, updates a model of their knowledge, and adapts what/how it teaches next. Core loop: **Question → Assess → Identify gaps → Teach the gap → Quiz → Evaluate → Update model → Repeat.**

---

## 2. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Language | **Python 3.11** (3.12 also fine; avoid 3.13 early on — some LangGraph/LC deps lag on new releases) | Stable, wide library support |
| Orchestration | **LangGraph** | Explicit state machine — perfect fit for your architecture diagram (each box = a node) |
| LLM layer | **LangChain** (or raw Anthropic/OpenAI SDK if you want less abstraction) | Prompt templates, structured output parsing |
| Structured I/O | **Pydantic v2** | Enforce schemas for assessments, quiz items, student model updates |
| Concept graph | **NetworkX** (start) → **Neo4j** (if you outgrow in-memory) | NetworkX needs zero infra; Neo4j pays off once graph queries get complex (prereq chains, topological sort) |
| Knowledge base / RAG | **Chroma** or **Qdrant** (local, free) + embeddings (OpenAI `text-embedding-3-small` or local `bge-small`) | Store textbook/course content for the Tutor Agent to ground explanations |
| Student model storage | **SQLite** (dev) → **Postgres** (prod) via **SQLAlchemy** | Simple relational schema: student, concept, mastery, history |
| API layer | **FastAPI** | Clean async endpoints, pairs naturally with Pydantic |
| Frontend | **Streamlit** (fast prototype) or **React + Tailwind** (polished/portfolio) | Streamlit to validate logic fast; React if this becomes a Fiverr deliverable |
| Testing | **pytest** | Test each node (assessment, difficulty estimator, evaluator) in isolation |
| Env/deps | **uv** or **poetry** | Reproducible environments |

---

## 3. Core Concepts to Learn Alongside Building

You don't need to master these before starting — pair each with the phase that needs it.

1. **Knowledge Tracing** — Bayesian Knowledge Tracing (BKT) is the simplest starting model (per-concept probability of mastery, updated with each observation). Deep Knowledge Tracing (DKT, RNN-based) is a stretch goal.
2. **Item Response Theory (IRT)** — for the Difficulty Estimator; models P(correct | student ability, item difficulty).
3. **Concept Graphs / Prerequisite Modeling** — DAG where edges = "must know X before Y." Powers the "teach calculus before backprop" behavior.
4. **RAG** — grounding tutor explanations in real course material instead of hallucinated content.
5. **Agent Planning (LangGraph state machines)** — conditional routing: if `mastery(concept) < threshold`, reroute to teach that concept instead of answering the original question.
6. **Feedback Loops / Online Learning** — updating the student model after every interaction, not just at test time.

---

## 4. Step-by-Step Build Plan

### Phase 0 — Environment Setup (Day 1)
- Python 3.11 venv, install `langgraph`, `langchain`, `pydantic`, `networkx`, `chromadb`, `fastapi`, `sqlalchemy`, `pytest`
- Repo structure:
```
adaptive-learning-agent/
├── src/
│   ├── graph/            # concept graph (nodes, edges, prereqs)
│   ├── models/            # Pydantic schemas
│   ├── agents/            # LangGraph nodes: assessor, tutor, quiz_gen, evaluator
│   ├── db/                 # student model persistence
│   ├── rag/                # retrieval over course content
│   └── api/                # FastAPI routes
├── tests/
├── data/                   # seed concept graph + course content
└── main.py
```

### Phase 1 — Concept Graph (Days 2–3)
- Define concepts as nodes, prerequisites as directed edges (NetworkX `DiGraph`).
- Seed manually for one domain (e.g., "Neural Networks 101": Linear Algebra → Calculus → Neural Networks → Backpropagation).
- Write a function `get_prerequisites(concept) -> List[concept]` (topological ancestors).

### Phase 2 — Student Model (Days 3–4)
- Pydantic schema: `StudentModel { student_id, mastery: Dict[concept, float 0-1], history: List[Interaction] }`
- Persist in SQLite via SQLAlchemy.
- This is the object every other component reads/writes.

### Phase 3 — Knowledge Assessment Node (Days 4–6)
- Input: student question (e.g., "Explain backpropagation").
- LLM call with structured output (Pydantic) → classify which concepts the question touches, and estimate current mastery signal from phrasing/history.
- Output: `{concept: status}` map like your example (✓ / ✗ / ?).

### Phase 4 — Difficulty Estimator (Days 6–7)
- Simple version: rule-based — if any prerequisite mastery < 0.5, difficulty = "too high, redirect."
- Stretch: basic IRT — estimate item difficulty from past student success rates on similar questions.

### Phase 5 — Tutor Agent (Days 7–10)
- LangGraph node with conditional routing:
  - If gap found → generate explanation for the *missing prerequisite*, not the original question.
  - If no gap → answer directly, optionally RAG-grounded.
- This is the "brain" — build it as a graph with explicit edges so routing logic is inspectable, not buried in one giant prompt.

### Phase 6 — Quiz Generator (Days 10–11)
- Given a concept, generate 2–3 questions (MCQ or short-answer) via structured LLM output.
- Difficulty scaled to estimated mastery (easier if mastery is low).

### Phase 7 — Evaluator (Days 11–12)
- Compare student answer to expected answer/rubric (LLM-graded or rule-based for MCQ).
- Output: correct/incorrect + confidence.

### Phase 8 — Update Loop (Days 12–13)
- On each evaluation, update `mastery[concept]` using a simple BKT-style Bayesian update (or even a basic exponential moving average to start).
- Persist to student model.
- Loop back: re-check if the original question can now be answered.

### Phase 9 — Wire the Full LangGraph (Days 13–15)
- Assemble all nodes into one `StateGraph`: Assessment → Concept Graph lookup → Difficulty Estimator → Tutor → Quiz → Evaluator → Update → (loop or answer original question).
- This is where your architecture diagram becomes literal code.

### Phase 10 — API + Frontend (Days 15–18)
- FastAPI endpoints: `POST /ask`, `POST /answer`, `GET /student/{id}/model`.
- Streamlit UI for a working demo (chat + a live "mastery dashboard" showing the concept graph with ✓/✗/? — this visual sells the project on Fiverr/portfolio).

### Phase 11 — Testing & Evaluation (Days 18–20)
- Unit tests per node (mock LLM calls).
- End-to-end scenario tests: seed a student with known gaps, verify the agent redirects correctly.
- Optional: build a small eval set of "question → expected teaching path" pairs to measure whether the agent routes correctly.

### Phase 12 — Polish for Delivery (Days 20–22)
- README with architecture diagram, demo GIF, setup instructions.
- If targeting Fiverr: package as a configurable template (swap concept graph/domain via a config file, not code changes).

---

## 5. Suggested Milestone Checkpoints
- **Week 1**: Concept graph + student model + assessment node working standalone.
- **Week 2**: Full LangGraph loop working end-to-end on one toy domain (backprop example).
- **Week 3**: API + UI + tests + polish, ready to demo.

---

## 6. Stretch Goals (if time allows)
- Swap rule-based mastery updates for real BKT/DKT.
- Multi-domain concept graphs (auto-extract prereqs from a syllabus via LLM).
- Spaced-repetition scheduling for review questions.
- Multi-student analytics dashboard (useful selling point for tutoring platforms).
