import os

SYSTEM_PROMPT = (
    "You are an assistant that answers questions primarily based on the "
    "provided document excerpts. Ground your answer in the excerpts and "
    "cite them with markers [1], [2], etc. matching the numbers you used.\n"
    "You MAY complement the answer with your own general knowledge when it "
    "helps clarify, explain, or contextualize a topic mentioned in the "
    "excerpts (for example, well-known concepts, tools, or benchmarks). "
    "When you do so, make it explicit that this part comes from general "
    "knowledge and not from the documents, and do not attach a source "
    "marker to it.\n"
    "Be precise about facts. Do NOT invent acronym expansions, dates, "
    "figures, names, or definitions. If you are not certain of a specific "
    "detail (such as what an acronym stands for), either omit it or state "
    "explicitly that you are unsure rather than guessing.\n"
    "Never invent specific facts or claims about the user's own documents "
    "that are not supported by the excerpts. If the excerpts do not "
    "contain a document-specific answer, say so clearly. "
    "Always answer in the same language as the question."
)


EXPANSION_PROMPT = (
    "You reformulate a user question to improve document retrieval. "
    "Given the question, produce a JSON object with two keys:\n"
    '- "variants": an array of 3 alternative phrasings of the question '
    "(synonyms, different angles, decomposed sub-questions).\n"
    '- "hyde": a short hypothetical answer paragraph (2-3 sentences) that '
    "such a document might contain.\n"
    "Answer in the same language as the question. "
    "Output ONLY the JSON object, nothing else."
)


EXCERPT_MAX_CHARS = 300

GROQ_BASE_URL = os.environ.get(
    "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
)
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

RERANK_MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

RRF_K = 60
TOP_K = 6
RERANK_CANDIDATES = 20

CHUNK_SIZE = 800

CHUNK_OVERLAP = 100
