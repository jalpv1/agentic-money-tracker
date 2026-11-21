from langchain_ollama import ChatOllama

from src.agent.tools import TOOLS


def create_model():
    return  ChatOllama(model="qwen3:30b-a3b", temperature=0, num_ctx=16384).bind_tools(TOOLS)