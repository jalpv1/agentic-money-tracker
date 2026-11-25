import time
import uuid

from langchain_core.messages import ToolMessage
from langgraph.errors import GraphRecursionError

from evals.models import Case, Run

def run_case(app, case: Case) -> Run:
    config = {"configurable": {"thread_id": uuid.uuid4().hex}, "recursion_limit": 12}
    run = Run()
    start = time.time()
    try:
        messages = []
        for question in case.questions:          # same thread_id = follow-up memory
            messages = app.invoke({"messages": [("user", question)]}, config)["messages"]
        run.reply = str(messages[-1].content)
        for m in messages:
            for tc in getattr(m, "tool_calls", None) or []:
                run.tool_calls.append({"name": tc["name"], "args": tc["args"]})
            if isinstance(m, ToolMessage):
                run.tool_outputs.append(str(m.content))
    except GraphRecursionError:
        run.error = "recursion limit"
    except Exception as e:                        # one broken case must not stop the run
        run.error = f"{type(e).__name__}: {e}"
    run.seconds = time.time() - start
    return run