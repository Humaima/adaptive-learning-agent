from src.config import FLASHCARD_INITIAL_INTERVAL_DAYS, FLASHCARD_EASE_MULTIPLIER


def compute_next_interval(current_interval_days: int, knew_it: bool) -> int:
    """
    Simple SM-2-style spaced repetition: knowing it doubles the gap until next
    review (so easy cards show up less and less); forgetting resets to the
    shortest interval so it comes back around soon.
    """
    if not knew_it:
        return FLASHCARD_INITIAL_INTERVAL_DAYS
    return max(FLASHCARD_INITIAL_INTERVAL_DAYS, round(current_interval_days * FLASHCARD_EASE_MULTIPLIER))