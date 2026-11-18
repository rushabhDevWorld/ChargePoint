import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://hygiene:hygiene@localhost:5432/hygiene"
)

# stations scoring below this are flagged as "poor"
POOR_SCORE_THRESHOLD = int(os.getenv("HYGIENE_THRESHOLD", "60"))
