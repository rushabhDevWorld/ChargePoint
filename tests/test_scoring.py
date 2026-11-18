from app.scoring import calculate_score


def test_healthy_station_gets_full_score():
    assert calculate_score("online", 50, 0) == 100


def test_offline_loses_fifty():
    assert calculate_score("offline", 50, 0) == 50


def test_latency_penalty_is_capped():
    assert calculate_score("online", 400, 0) == 95
    assert calculate_score("online", 100_000, 0) == 75


def test_error_penalty_is_capped():
    assert calculate_score("online", 50, 5) == 90
    assert calculate_score("online", 50, 500) == 75


def test_score_never_negative():
    assert calculate_score("offline", 100_000, 500) >= 0
