import os
from typing import Annotated, TypedDict, Literal, List, Optional, Tuple
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from tools import all_tools, news_tools, general_tools

load_dotenv()

# ── Prompts ────────────────────────────────────────────────────────────────────

CLASSIFIER_PROMPT = """You are a query classifier for NewsGenie, an AI news assistant.

Classify the user's message as exactly one of:
- "news"    → user wants current events, headlines, breaking news, recent updates on any topic
- "general" → user is asking a general question, wants an explanation, or is making conversation

Reply with ONLY one word: news  OR  general"""

NEWS_SYSTEM_PROMPT = """\
You are NewsGenie, an AI-powered news assistant. Your mission:
1. Use available tools to fetch real, current news before answering
2. Present news in a structured, easy-to-read format
3. Attribute sources and note publication dates
4. Highlight key takeaways and why the story matters
5. Remain balanced and factual — flag speculation clearly

When news tools fail or return no results, fall back to web_search and say so.
Always prefer fresh data from tools over your training knowledge for current events."""

GENERAL_SYSTEM_PROMPT = """\
You are NewsGenie, a knowledgeable AI assistant.
- Answer questions clearly and concisely
- Use web_search for facts you're not certain about or that may have changed
- Keep responses focused and helpful
- You can switch modes naturally if the user pivots to a news question"""

# ── State ──────────────────────────────────────────────────────────────────────

class NewsGenieState(TypedDict):
    messages: Annotated[list, add_messages]
    query_type: str        # "news" | "general"
    category: str          # user-selected news category
    active_agent: str      # tracks which agent called tools last


# ── LLM factory ───────────────────────────────────────────────────────────────

def _llm(model: str = "gpt-4o", temperature: float = 0.3) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=temperature,
    )


# ── Agent builder ──────────────────────────────────────────────────────────────

def build_agent():
    classifier = _llm("gpt-4o-mini", temperature=0)
    news_llm = _llm("gpt-4o").bind_tools(all_tools)
    general_llm = _llm("gpt-4o").bind_tools(general_tools)

    # 1. Classify the latest user message
    def classify_node(state: NewsGenieState) -> dict:
        last_human = next(
            (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
            "",
        )
        try:
            resp = classifier.invoke([
                SystemMessage(content=CLASSIFIER_PROMPT),
                HumanMessage(content=last_human),
            ])
            qt = resp.content.strip().lower()
            qt = "news" if "news" in qt else "general"
        except Exception:
            qt = "news"
        return {"query_type": qt, "active_agent": qt}

    # 2. Routing after classification
    def route_after_classify(state: NewsGenieState) -> Literal["news_agent", "general_agent"]:
        return "news_agent" if state.get("query_type") == "news" else "general_agent"

    # 3. News agent — fetches and summarises news
    def news_agent_node(state: NewsGenieState) -> dict:
        category = state.get("category", "general")
        system = SystemMessage(
            content=f"{NEWS_SYSTEM_PROMPT}\n\nUser's selected category: **{category.title()}**"
        )
        # Strip any prior system messages to avoid duplication
        history = [m for m in state["messages"] if not isinstance(m, SystemMessage)]
        response = news_llm.invoke([system] + history)
        return {"messages": [response], "active_agent": "news"}

    # 4. General agent — answers conversational / factual queries
    def general_agent_node(state: NewsGenieState) -> dict:
        system = SystemMessage(content=GENERAL_SYSTEM_PROMPT)
        history = [m for m in state["messages"] if not isinstance(m, SystemMessage)]
        response = general_llm.invoke([system] + history)
        return {"messages": [response], "active_agent": "general"}

    # 5. After tools, return to whichever agent was active
    def route_after_tools(state: NewsGenieState) -> Literal["news_agent", "general_agent"]:
        return "news_agent" if state.get("active_agent") == "news" else "general_agent"

    tool_node = ToolNode(all_tools)

    # ── Graph ──────────────────────────────────────────────────────────────────
    g = StateGraph(NewsGenieState)
    g.add_node("classify",       classify_node)
    g.add_node("news_agent",     news_agent_node)
    g.add_node("general_agent",  general_agent_node)
    g.add_node("tools",          tool_node)

    g.set_entry_point("classify")
    g.add_conditional_edges("classify",      route_after_classify)
    g.add_conditional_edges("news_agent",    tools_condition)
    g.add_conditional_edges("general_agent", tools_condition)
    g.add_conditional_edges(
        "tools", route_after_tools,
        {"news_agent": "news_agent", "general_agent": "general_agent"},
    )

    return g.compile()


# ── Public API ─────────────────────────────────────────────────────────────────

def chat(
    user_message: str,
    category: str = "general",
    history: Optional[List[BaseMessage]] = None,
    on_step=None,
) -> Tuple[str, List[BaseMessage]]:
    """
    Send a message to NewsGenie and get a reply.

    Returns (reply_text, updated_history) so the caller can maintain context.
    """
    agent = build_agent()

    messages = list(history or [])
    messages.append(HumanMessage(content=user_message))

    state: NewsGenieState = {
        "messages": messages,
        "query_type": "",
        "category": category,
        "active_agent": "",
    }

    reply = ""
    for event in agent.stream(state):
        for node, output in event.items():
            if on_step:
                if node == "classify":
                    on_step(f"Classified as: **{output.get('query_type', '').upper()}**")
                elif node in ("news_agent", "general_agent"):
                    for msg in output.get("messages", []):
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                on_step(f"Tool: `{tc['name']}`")
            if node in ("news_agent", "general_agent"):
                for msg in output.get("messages", []):
                    if (
                        hasattr(msg, "content")
                        and msg.content
                        and not (hasattr(msg, "tool_calls") and msg.tool_calls)
                    ):
                        reply = msg.content

    updated_history = messages + [AIMessage(content=reply)] if reply else messages
    return reply or "I couldn't generate a response. Please try again.", updated_history
