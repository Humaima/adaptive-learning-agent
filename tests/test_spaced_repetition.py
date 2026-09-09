from src.study_tools.spaced_repetition import compute_next_interval

def test_knowing_it_doubles_interval():
    assert compute_next_interval(2, True) == 4

def test_forgetting_resets_to_initial():
    assert compute_next_interval(10, False) == 1

def test_minimum_interval_enforced():
    assert compute_next_interval(0, True) >= 1