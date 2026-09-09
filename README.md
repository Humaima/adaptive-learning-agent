# 📖 Adaptive Learning Agent

An AI tutor that doesn't just answer questions — it diagnoses what a student
actually doesn't understand, teaches the missing prerequisite first, quizzes
them to confirm it landed, and only then answers what they originally asked.

Built with **LangGraph**, **FastAPI**, **React**, and **Groq (`openai/gpt-oss-120b`)**.

## Live Demo

- App: [https://adaptive-learning-agent-lake.vercel.app/](#)
- API docs: [https://adaptive-learning-agent-ux86.onrender.com/docs](#)

![Demo](docs/demo.gif) 

## How It Works

``` bash
Student Question
↓
Knowledge Assessment ──uses──▶ Concept Graph (prerequisite DAG)
↓
Difficulty Estimator
↓
Tutor Agent ──▶ explains the RIGHT concept at the RIGHT difficulty
↓
Quiz Generator
↓
Student Answers
↓
Evaluator
↓
Update Student Model ──▶ loops back if a prerequisite gap remains
```

If a student asks about backpropagation but hasn't mastered calculus, the
agent silently teaches calculus first — the same behavior a good human tutor
would default to — then works back up to the original question.

## Features

- 🧠 Adaptive teaching that redirects to unmastered prerequisites automatically
- 📊 Live mastery dashboard per concept, per domain
- 📝 Save any tutor explanation as a note
- 🃏 Auto-generated flashcards with spaced repetition scheduling
- 📈 Full quiz history with accuracy tracking
- 🔐 Real authentication (JWT access + refresh tokens)
- 🐳 Fully Dockerized, deployed on Render + Vercel

## Tech Stack

| Layer | Tech |
|---|---|
| Agent orchestration | LangGraph (state machine + human-in-the-loop interrupts) |
| LLM | Groq — `openai/gpt-oss-120b` |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL |
| Frontend | React (Vite), react-router |
| Auth | JWT (access + refresh), bcrypt |
| Deployment | Docker, Render (API + DB), Vercel (frontend) |

## Project Structure

```
adaptive-learning-agent/
├── src/
│ ├── graph/ # concept prerequisite graph
│ ├── agents/ # LangGraph nodes: assessment, tutor, quiz, evaluator, etc.
│ ├── db/ # SQLAlchemy models + repository layer
│ ├── auth/ # JWT + password hashing
│ ├── api/ # FastAPI routes
│ └── study_tools/ # spaced repetition logic
├── frontend/ # React app
├── data/ # concept dataset, eval cases
├── tests/ # pytest suite (mocked LLM — free, fast, deterministic)
├── scripts/ # manual test scripts, dataset generation, eval runner
└── docker-compose.yml
```

## Local Setup

### Backend
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Env
```
Copy `.env.example` to `.env` and fill in `GROQ_API_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`.
```

### Starting the website
```
python -m src.db.init_db
python -m uvicorn src.api.main:app --reload --port 8000
```

### Frontend
```
cd frontend
npm install
npm run dev
```

### Or, everything at once with Docker
```
docker compose up --build
```

## Testing
```
pytest # fast, mocked-LLM unit tests
python -m scripts.run_eval # real-model accuracy eval (costs a few Groq calls)
```

## Roadmap

- [ ] Revocable refresh tokens (currently stateless)
- [ ] Real-time streaming of tutor explanations
- [ ] Teacher/admin dashboard for curriculum authoring
- [ ] Mobile app (React Native)

## License
```
MIT
```
Also create a matching .env.example at the project root (documents required vars without leaking real secrets):

```
GROQ_API_KEY=
JWT_SECRET_KEY=
DATABASE_URL=postgresql://postgres:devpassword@localhost:5432/adaptive_tutor
```
