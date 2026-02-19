# Project: DIY Project Planner – Phase 3 (RAG Project Planning)

## High-level goal

Extend the DIY Project Planner to provide **AI-powered project planning** based on free-form descriptions of the user's current situation and goals.

**Phase 3 User Flow:**
1. On the Shopping List page, user sees a free-form text input
2. Above the input: *"Describe what you're trying to do and materials/sizes you're working with (e.g., 'replace ½ inch copper pipe leaking under kitchen sink with PEX')"*
3. "Generate plan" button → calls `POST /api/generate-plan/`
4. Backend invokes modular RAG pipeline in rag_search.py → returns project plan
5. Display results below text box

**Key requirements:**
- **Modular RAG backend** (easy model swapping)
- **Frontend integration** with existing Shopping List page
- **Structured output** (materials, tools, warnings, steps)

This builds directly on Phase 1 (shopping lists) + Phase 2 (product search).

---

## Tech stack additions (Phase 3)

**Frontend:** React (existing)
**Backend:** Django REST Framework + **RAG pipeline**
**RAG Components: Prompt, ChromaDB, ChatOpenAI, LangChain**