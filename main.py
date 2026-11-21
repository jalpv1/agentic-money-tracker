import os
import sys

from langgraph.errors import GraphRecursionError

from src.agent.agent import build_agent
from src.data import sync

CONFIG = {"configurable": {"thread_id": "local-chat"}, "recursion_limit": 12}
DEBUG = os.environ.get("DEBUG") == "1"  # item 10: the switch


def ask(app, text: str) -> None:
    payload = {"messages": [("user", text)]}
    if DEBUG:  # item 10: raw steps
        for chunk in app.stream(payload, CONFIG, stream_mode="updates"):
            print(chunk)
    else:  # item 10: clean answer
        result = app.invoke(payload, CONFIG)
        print(f"bot> {result['messages'][-1].content}\n")


def chat() -> None:  # item 7: the loop
    app = build_agent()
    while True:
        text = input("you> ").strip()
        if text.lower() in {"exit", "quit"}:
            break
        if not text:
            continue
        try:
            ask(app, text)
        except GraphRecursionError:
            print("bot> I got stuck on that one. Try rephrasing.\n")


if __name__ == "__main__":
    if sys.argv[1:] == ["sync"]:
        print(f"{sync()} new transactions")
    else:
        chat()
