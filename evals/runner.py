import time
import uuid

from langchain_core.messages import ToolMessage
from langgraph.errors import GraphRecursionError

from evals.types import Case, Run

def run_case(app, case: Case) -> Run:

