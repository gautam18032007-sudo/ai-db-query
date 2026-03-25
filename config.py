import os
from dotenv import load_dotenv

load_dotenv()

# AlloyDB / PostgreSQL
DB_HOST     = os.getenv("DB_HOST",     "YOUR_ALLOYDB_IP")
DB_PORT     = int(os.getenv("DB_PORT", 5432))
DB_NAME     = os.getenv("DB_NAME",     "aidb")
DB_USER     = os.getenv("DB_USER",     "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "YOUR_PASSWORD")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

TABLE_NAME = "products"
# No Anthropic API key here — AI calls are made from the frontend browser.