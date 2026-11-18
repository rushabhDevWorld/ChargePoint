"""Network hygiene score: 0 (bad) to 100 (perfect).

  offline            -> -50
  latency over 200ms -> -1 per extra 40ms, capped at -25
  errors             -> -2 per error, capped at -25

The weights are a judgement call, not tuned on real data. With the default
threshold of 60, an offline station is always flagged once it has a few errors
or high latency, and an online station is only flagged if it is really noisy.
"""

OFFLINE_PENALTY = 50
LATENCY_OK_MS = 200
LATENCY_STEP_MS = 40
MAX_LATENCY_PENALTY = 25
ERROR_PENALTY = 2
MAX_ERROR_PENALTY = 25


def calculate_score(connectivity_status: str, latency_ms: int, error_count: int) -> int:
    score = 100

    if connectivity_status == "offline":
        score -= OFFLINE_PENALTY

    if latency_ms > LATENCY_OK_MS:
        score -= min(MAX_LATENCY_PENALTY, (latency_ms - LATENCY_OK_MS) // LATENCY_STEP_MS)

    score -= min(MAX_ERROR_PENALTY, error_count * ERROR_PENALTY)

    return max(score, 0)
