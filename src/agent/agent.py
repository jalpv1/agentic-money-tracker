from src.agent.model import create_model


from datetime import date

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.model import create_model
from src.agent.state import State
from src.agent.tools import TOOLS

llm_with_tools = create_model().bind_tools(TOOLS)

SYSTEM_PROMPT = """You are a personal finance assistant for the user's bank transactions.

Rules:
- Never calculate totals, averages or counts yourself. Always use the tools.
- If unsure which categories or merchants exist, call data_overview first.
- Only use category names returned by data_overview.
- If a tool returns nothing, say so. Do not guess.
- Today is {today}. Convert relative dates ("last month") to YYYY-MM-DD before calling tools.
- Always state the currency.
- Reply in the user's language.
"""


def agent(state: State):
    system = SystemMessage(SYSTEM_PROMPT.format(today=date.today().isoformat()))
    response = llm_with_tools.invoke([system, *state["messages"]])
    return {"messages": [response]}


def route(state: State) -> str:
    return "tools" if state["messages"][-1].tool_calls else END


def build_agent():
    g = StateGraph(State)
    g.add_node("agent", agent)
    g.add_node("tools", ToolNode(TOOLS))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", route, ["tools", END])
    g.add_edge("tools", "agent")
    return g.compile(checkpointer=InMemorySaver())
