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