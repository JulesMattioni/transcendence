import os

SYSTEM_PROMPT = (
    "You are an assistant that answers questions based ONLY on the "
    "provided document excerpts. If the excerpts do not contain the "
    "answer, say so clearly instead of inventing one. Always answer in "
    "the same language as the question. Cite your sources with markers "
    "[1], [2], etc. matching the numbers of the excerpts you used."
)

EXCERPT_MAX_CHARS = 300

GROQ_BASE_URL = os.environ.get(
    "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
)
GROQ_MODEL = os.environ.get(
    "GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"
)
