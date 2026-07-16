import urllib.request
import json

# TO LAUNCH: docker exec -i transcendence-rag-1 python < test_query.py

payload = json.dumps({
    "question": "What benchmarks are used to evaluate the agent, and what is the difference between them?",
    "organisation_id": 1,
}).encode()

req = urllib.request.Request(
    "http://localhost:8000/query",
    data=payload,
    headers={"Content-Type": "application/json"},
)
resp = json.load(urllib.request.urlopen(req, timeout=120))

print("===== ANSWER =====")
print(resp["answer"])
print()
print("===== SOURCES =====")
for i, s in enumerate(resp["sources"], 1):
    excerpt = s["excerpt"][:120].replace("\n", " ")
    print("[%d] file_id=%s chunk_index=%s" % (i, s["file_id"], s["chunk_index"]))
    print("     %s ..." % excerpt)
