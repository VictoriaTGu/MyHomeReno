# Project: DIY Project Planner – Phase 3 (RAG Project Planning)

## High-level goal

Extend the DIY Project Planner to provide **AI-powered project planning** based on free-form descriptions of the user's current situation and goals.

**Phase 3 User Flow:**
1. On the Project Selection page, user sees a free-form text input
2. Above the input: *"Don’t see your project below? Describe what you’re trying to do and materials/sizes you're working with (e.g., 'replace ½ inch copper pipe leaking under kitchen sink with PEX')"*
3. "Generate plan" button → calls `POST /api/generate-plan/`
4. Backend invokes modular RAG pipeline in rag_search.py → returns project plan
5. Display results below text box
6. Allow user to revise their input and click the "Generate plan" button again if they wish
7. Display a button below the plan results entitled 'Start Project' 
-> Call `POST /api/projects/` with the list of materials provided in the project plan. It should return the serialized project and newly created 
`ProjectMaterial`s. If that succeeds then
-> Call `POST /api/shopping-lists/` with `project_id`=`new_id` → navigate to shopping list page. 

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