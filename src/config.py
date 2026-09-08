# Mastery threshold: score at or above this = considered "mastered" (✓)
MASTERY_THRESHOLD = 0.7

# Retry settings for Groq API calls
LLM_MAX_RETRIES = 4
LLM_RETRY_MIN_WAIT = 2   # seconds
LLM_RETRY_MAX_WAIT = 20  # seconds

# Difficulty banding — used to decide how hard a taught concept or quiz question should be
DIFFICULTY_EASY_MAX = 0.3     # mastery below this -> teach/quiz at EASY level
DIFFICULTY_HARD_MIN = 0.7     # mastery at or above this -> teach/quiz at HARD (challenge) level
                               # anything in between -> MEDIUM

# Default difficulty to use when a concept has never been assessed (mastery = None)
DEFAULT_DIFFICULTY_FOR_UNKNOWN = "easy"

# Default difficulty to use when a concept has never been assessed (mastery = None)
DEFAULT_DIFFICULTY_FOR_UNKNOWN = "easy"

# Quiz generation settings
NUM_QUIZ_QUESTIONS = 3

# Short-answer grading: LLM returns a 0.0-1.0 correctness score.
# At or above this threshold, the answer counts as "correct" for mastery-update purposes.
SHORT_ANSWER_CORRECT_THRESHOLD = 0.7

# Mastery update (EMA-style: blends prior belief with new evidence)
MASTERY_LEARNING_RATE = 0.3    # how much weight new evidence gets vs. the existing score
INITIAL_MASTERY_PRIOR = 0.5    # neutral starting point when a concept has never been assessed


# Safety Cap: max teach->quiz->evaluate->update cycles per question,
# in case of a misbehaving concept graph or LLM drift causing an unexpected loop.
MAX_LOOP_ITERATIONS = 5

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day