"""REPL interactif pour tester le RAG en CLI (streaming + conversation).

Usage:
    docker exec -i transcendence-rag-1 sh -c 'cat > /app/chat_cli.py' < chat_cli.pyo
    puis
    docker exec -it transcendence-rag-1 python /app/chat_cli.py

Options via variables d'environnement :
    RAG_URL   (defaut http://localhost:8000)
    ORG_ID    (defaut 1)

Commandes dans le REPL :
    /new      demarre une nouvelle conversation (oublie le contexte)
    /id       affiche le conversation_id courant
    /quit     quitte (ou Ctrl-D)
"""

import json
import os
import sys

import httpx

RAG_URL = os.environ.get("RAG_URL", "http://localhost:8000").rstrip("/")
ORG_ID = int(os.environ.get("ORG_ID", "1"))

STREAM_URL = f"{RAG_URL}/query/stream"

# Petites couleurs ANSI (ignorees si le terminal ne suit pas).
DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def ask(question: str, conversation_id):
    """Envoie la question en streaming, affiche la reponse au fil de l'eau.

    Retourne (conversation_id, sources) pour le tour suivant.
    """
    payload = {"question": question, "organisation_id": ORG_ID}
    if conversation_id is not None:
        payload["conversation_id"] = conversation_id

    new_conv_id = conversation_id
    sources = []
    printed_answer_header = False

    try:
        with httpx.stream(
            "POST", STREAM_URL, json=payload, timeout=180.0
        ) as resp:
            if resp.status_code != 200:
                body = resp.read().decode(errors="ignore")
                print(f"{YELLOW}[erreur HTTP {resp.status_code}] {body}{RESET}")
                return conversation_id, []

            event = None
            for line in resp.iter_lines():
                if line.startswith("event:"):
                    event = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    raw = line[len("data:"):].strip()
                    if not raw:
                        continue
                    data = json.loads(raw)
                    if event == "conversation":
                        new_conv_id = data["conversation_id"]
                    elif event == "sources":
                        sources = data["sources"]
                    elif event == "token":
                        if not printed_answer_header:
                            print(f"{BOLD}{GREEN}RAG:{RESET} ", end="")
                            printed_answer_header = True
                        print(data["text"], end="", flush=True)
                    elif event == "done":
                        break
    except httpx.HTTPError as e:
        print(f"{YELLOW}[erreur reseau] {e}{RESET}")
        return conversation_id, []

    print()  # newline apres la reponse streamee

    if sources:
        print(f"\n{DIM}Sources :{RESET}")
        for i, s in enumerate(sources, 1):
            excerpt = (s.get("excerpt") or "").replace("\n", " ")[:90]
            print(
                f"{DIM}  [{i}] file_id={s['file_id']} "
                f"chunk={s['chunk_index']} | {excerpt}...{RESET}"
            )

    return new_conv_id, sources


def main():
    print(f"{BOLD}{CYAN}=== RAG chat CLI ==={RESET}")
    print(f"{DIM}URL={RAG_URL}  org_id={ORG_ID}{RESET}")
    print(f"{DIM}Commandes : /new  /id  /quit (ou Ctrl-D){RESET}\n")

    conversation_id = None

    while True:
        try:
            question = input(f"{BOLD}{CYAN}Vous:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Bye.{RESET}")
            break

        if not question:
            continue
        if question in ("/quit", "/exit"):
            print(f"{DIM}Bye.{RESET}")
            break
        if question == "/new":
            conversation_id = None
            print(f"{DIM}Nouvelle conversation.{RESET}\n")
            continue
        if question == "/id":
            print(f"{DIM}conversation_id = {conversation_id}{RESET}\n")
            continue

        conversation_id, _ = ask(question, conversation_id)
        print()


if __name__ == "__main__":
    main()
