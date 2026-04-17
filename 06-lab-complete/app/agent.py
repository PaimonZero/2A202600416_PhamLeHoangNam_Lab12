"""
LangGraph Agent for Travel Assistant

Integrates LangChain + LangGraph for agentic chat with tool calling.
Supports OpenAI API + GitHub PAT for LLM access.
"""

import os
import logging
from typing import Annotated, TypedDict
from pathlib import Path

from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig

from app.tools import search_flights, search_hotels, calculate_budget

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
# State & Model Setup
# ─────────────────────────────────────────────────────────

class AgentState(TypedDict):
    """Internal graph state for LangGraph."""
    messages: Annotated[list, add_messages]


def get_model() -> ChatOpenAI:
    """
    Setup LangChain OpenAI model instance.
    Priority: GitHub PAT → OpenAI API Key
    """
    github_pat = os.getenv("GITHUB_PAT")
    if github_pat:
        logger.info("Using GitHub PAT for LLM")
        return ChatOpenAI(
            model="gpt-4.1",
            api_key=SecretStr(github_pat),
            base_url="https://models.inference.ai.azure.com"
        )
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        logger.info("Using OpenAI API Key for LLM")
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=SecretStr(openai_api_key)
        )
    
    logger.warning("No API key found, falling back to mock responses")
    # Return None - calling code should handle fallback
    return None


def load_system_prompt() -> str:
    """Load system prompt from file."""
    prompt_path = Path(__file__).parent / "system_prompt.txt"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"system_prompt.txt not found at {prompt_path}")
        return "You are a helpful travel assistant."


# ─────────────────────────────────────────────────────────
# Agent Nodes
# ─────────────────────────────────────────────────────────

def agent_node(state: AgentState, llm_with_tools) -> dict:
    """
    Main agent node - processes messages and calls tools if needed.
    Prepends system prompt if not already present.
    """
    messages = state.get("messages", [])
    
    # Ensure system prompt is first
    if not messages or not isinstance(messages[0], SystemMessage):
        system_prompt = load_system_prompt()
        messages = [SystemMessage(content=system_prompt)] + list(messages)
    
    try:
        response = llm_with_tools.invoke(messages)
        
        # Log tool calls for observability
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", "unknown")
                logger.debug(f"Tool called: {tool_name}")
        
        return {"messages": [response]}
    
    except Exception as error:
        logger.error(f"Agent node error: {error}", exc_info=True)
        return {
            "messages": [{
                "role": "assistant",
                "content": "Xin lỗi, đã xảy ra lỗi trong hệ thống TravelBuddy."
            }]
        }


def create_agent():
    """
    Factory function to create and compile the LangGraph agent.
    
    Returns:
        tuple: (agent_graph, memory_saver)
    """
    # Initialize model
    llm = get_model()
    if not llm:
        raise ValueError("No LLM API key configured. Set OPENAI_API_KEY or GITHUB_PAT.")
    
    # Bind tools
    tools_list = [search_flights, search_hotels, calculate_budget]
    llm_with_tools = llm.bind_tools(tools_list)
    
    # Create agent node with closure over llm_with_tools
    def agent_node_wrapper(state: AgentState) -> dict:
        return agent_node(state, llm_with_tools)
    
    # Build graph
    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node_wrapper)
    builder.add_node("tools", ToolNode(tools_list))
    
    # Define flow
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    
    # Compile with memory
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    
    logger.info("Agent graph created successfully")
    return graph, memory


def invoke_agent(graph, messages: list, session_id: str) -> dict:
    """
    Invoke agent with a list of messages.
    
    Args:
        graph: Compiled LangGraph
        messages: List of messages
        session_id: Thread ID for conversation tracking
    
    Returns:
        dict: Result with messages list
    """
    try:
        config = {"configurable": {"thread_id": session_id}}
        result = graph.invoke({"messages": messages}, config=config)
        return result
    except Exception as error:
        logger.error(f"Error invoking agent: {error}", exc_info=True)
        raise
