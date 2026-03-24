import os
from dotenv import load_dotenv

load_dotenv()

# AlloyDB / PostgreSQL connection settings
DB_HOST = os.getenv("DB_HOST", "YOUR_ALLOYDB_IP")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "aidb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "YOUR_PASSWORD")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Anthropic API key (used by ai.py to generate SQL from natural language)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")

# Dataset table name seeded in AlloyDB
TABLE_NAME = "products"