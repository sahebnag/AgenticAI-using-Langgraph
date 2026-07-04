# 🗞️ NewsGenie — AI-Powered Information & News Assistant

NewsGenie is an agentic AI application that delivers real-time, curated news and answers general queries through a unified conversational interface. Built with **LangGraph**, **OpenAI GPT-4o**, **NewsAPI**, and **Streamlit**.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [LangGraph Workflow](#langgraph-workflow)
- [Tools](#tools)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [Usage Guide](#usage-guide)
- [Error Handling & Fallbacks](#error-handling--fallbacks)
- [Tech Stack](#tech-stack)

---

## Overview

People struggle to keep up with real-time, reliable news in today's fast-paced world. NewsGenie solves this by combining:

- An **AI chatbot** that distinguishes news queries from general questions
- A **real-time NewsAPI integration** for structured, sourced headlines
- A **DuckDuckGo web search fallback** that keeps the app functional even without a NewsAPI key
- A **LangGraph-based agentic workflow** that routes, fetches, and synthesises information intelligently
- A **Streamlit chat interface** with session memory, category selection, and graceful error handling

---

## Features

| Feature | Description |
|---|---|
| Query classification | GPT-4o-mini automatically decides if a query is news-related or general |
| 7 news categories | Technology, Finance, Sports, Health, Science, Entertainment, General |
| Real-time headlines | Top-5 articles per category via NewsAPI with source & date attribution |
| Keyword news search | Search any topic across all NewsAPI sources |
| Web search fallback | DuckDuckGo search activates automatically when NewsAPI is unavailable |
| Conversation memory | Full multi-turn context preserved across the session |
| Streamlit chat UI | Native `st.chat_message` interface with real-time agent status |
| Session management | Clear conversation button resets both display and LangChain history |
| Error handling | Distinct messages for auth errors, rate limits, and missing packages |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit UI (app.py)               │
│  ┌──────────┐  ┌──────────────────┐  ┌───────────┐  │
│  │ Sidebar  │  │   Chat Interface │  │  History  │  │
│  │ API Keys │  │  st.chat_message │  │  Session  │  │
│  │ Category │  │  st.chat_input   │  │  State    │  │
│  └──────────┘  └──────────────────┘  └───────────┘  │
└────────────────────────┬────────────────────────────┘
                         │ chat(user_message, category, history)
                         ▼
┌─────────────────────────────────────────────────────┐
│              LangGraph Agent (agent.py)              │
│                                                     │
│   [classify] ──► [news_agent]  ──► [tools] ──┐      │
│       │                                      │      │
│       └────────► [general_agent] ◄───────────┘      │
└─────────────────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
  get_top_headlines  search_news   web_search
     (NewsAPI)       (NewsAPI)    (DuckDuckGo)
```

---

## LangGraph Workflow

The agent is built as a stateful directed graph with four nodes:

```
START
  │
  ▼
[classify]          ← GPT-4o-mini classifies query as "news" or "general"
  │
  ├─ "news"    ──► [news_agent]    ← GPT-4o + all 3 tools
  │                     │
  └─ "general" ──► [general_agent] ← GPT-4o + web_search only
                        │
                    (tool calls?)
                        │ yes
                        ▼
                     [tools]       ← ToolNode executes the tool
                        │
                   (route back to whichever agent was active)
                        │
                    (no more tool calls)
                        │
                        ▼
                       END
```

### State Schema

```python
class NewsGenieState(TypedDict):
    messages:     list        # full conversation (LangChain messages)
    query_type:   str         # "news" | "general"
    category:     str         # user-selected category
    active_agent: str         # tracks which agent invoked tools last
```

### Routing Logic

- **After classify** → `news_agent` if `query_type == "news"`, else `general_agent`
- **After tools** → back to whichever agent set `active_agent` (enables multi-step tool use)
- **After agent** → `tools` if tool calls present, else `END`

---

## Tools

### `get_top_headlines(category)`
Fetches the top 5 headlines for a given category.

- **Primary**: NewsAPI `/v2/top-headlines?category=<category>`
- **Fallback**: DuckDuckGo search for `"latest <category> news today"`
- Returns: title, source, publication date, description, article URL

### `search_news_by_keyword(query)`
Searches all NewsAPI sources for articles matching a keyword or phrase.

- **Primary**: NewsAPI `/v2/everything?q=<query>&sortBy=publishedAt`
- **Fallback**: DuckDuckGo search
- Returns: top 5 matching articles with metadata

### `web_search(query)`
General-purpose web search for supplementary context or general queries.

- **Source**: DuckDuckGo (via `langchain-community`)
- Used by both agents; sole tool available to the general agent

---

## Project Structure

```
newsgenie/
├── app.py              # Streamlit UI — chat interface, sidebar, session management
├── agent.py            # LangGraph agent — classify, route, news/general nodes
├── tools.py            # Tool definitions — NewsAPI + DuckDuckGo with fallbacks
├── requirements.txt    # Python dependencies
├── .env                # API keys (not committed to version control)
└── venv/               # Python virtual environment
```

---

## Setup & Installation

### Prerequisites

- Python 3.8 or higher
- An **OpenAI API key** — [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- A **NewsAPI key** *(optional but recommended)* — free tier at [newsapi.org](https://newsapi.org)

### 1. Clone / navigate to the project

```bash
cd newsgenie
```

### 2. Create and activate virtual environment

```bash
# Create
python -m venv venv

# Activate — Windows PowerShell
.\venv\Scripts\Activate.ps1

# Activate — Windows Command Prompt
.\venv\Scripts\activate.bat

# Activate — macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

Create a `.env` file in the project root:

```env
# Required — OpenAI API key
OPENAI_API_KEY=sk-...

# Optional but recommended — NewsAPI key (free at newsapi.org)
NEWS_API_KEY=your_newsapi_key_here
```

> **Without a NewsAPI key** the app still works — it falls back to DuckDuckGo web search automatically, though results are less structured (no source attribution or article links).

API keys can also be entered directly in the app's sidebar at runtime.

---

## Running the App

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501** by default.

---

## Usage Guide

### News queries
Ask anything that involves current events — the classifier will route it to the news agent, which fetches live data before responding.

```
"Show me the latest technology news"
"What happened in the stock market today?"
"Give me today's top sports headlines"
"What's the latest on AI regulation?"
```

### General queries
Any non-news question is routed to the general agent, which uses web search when needed.

```
"What is machine learning?"
"Explain how interest rates affect inflation"
"Who founded OpenAI?"
```

### Category selector
Use the **sidebar radio buttons** to set your preferred news category. The active category is passed to the news agent as context, so asking "show me the news" will fetch headlines for your selected category.

### Conversation memory
NewsGenie maintains the full conversation history within a session. You can ask follow-up questions naturally:

```
User:  "What's happening in AI?"
Genie: [fetches AI news]
User:  "Tell me more about the first story"
Genie: [responds with context from previous exchange]
```

Click **🗑️ Clear conversation** in the sidebar to start a fresh session.

---

## Error Handling & Fallbacks

| Scenario | Behaviour |
|---|---|
| NewsAPI key missing | Falls back to DuckDuckGo web search silently |
| NewsAPI returns no results | Falls back to DuckDuckGo web search |
| NewsAPI request timeout / error | Falls back to DuckDuckGo web search |
| DuckDuckGo unavailable | Returns descriptive error message in response |
| Invalid OpenAI API key | Shows "Invalid or missing OpenAI API key" error banner |
| OpenAI rate limit hit | Shows "Rate limit hit, please wait" warning banner |
| Missing Python package | Shows package name and install command |
| Classifier fails | Defaults to "news" mode to favour retrieval over silence |

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | OpenAI GPT-4o (agents), GPT-4o-mini (classifier) |
| Agent framework | LangGraph 1.x |
| LLM integration | LangChain + langchain-openai |
| News data | NewsAPI.org (`/v2/top-headlines`, `/v2/everything`) |
| Web search | DuckDuckGo via langchain-community + ddgs |
| Frontend | Streamlit 1.x |
| Environment | python-dotenv |
| HTTP client | requests |
