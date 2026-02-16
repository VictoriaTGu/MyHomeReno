# Project: DIY Project Planner – Phase 1 (Shopping List + Store Integration)

## High-level goal

Build a web app that helps users prepare for home DIY projects by:

1. Selecting a predefined project (e.g., “Replace a section of copper pipe”, “Install new vanity”).
2. Viewing an **editable** shopping list of tools & materials for that project.
3. Keeping track of what materials and quantities of materials the user already has across projects. 
4. Optionally adding/removing materials from the shopping list or changing quantities of materials.

This context file is for **Phase 1 only**:
- Focus on project selection and shopping-list editing

---

## Tech stack

- Frontend: React with a simple component hierarchy.
- Backend: Django REST Framework (Python) with PostgreSQL.
- Database: PostgreSQL on local dev.

---

## Data model (Phase 1)

### Projects

Represents a DIY project template.

Fields (Django model: `Project`):
- `id`: PK
- `name`: string
- `description`: text (optional)
- `img`: string (nullable) - pointing to a url or file path

### Materials

Represents a generic material or tool that can appear in multiple projects. An initial set of Materials will be pre-populated in the database.

Fields (Django model: `Material`):
- `id`: PK
- `name`: string (required, e.g. "1/2\" copper pipe", "SharkBite 1/2\" coupler", "pipe cutter")
- `category`: string (required, e.g. "fitting", "tool")
- `store`: string (optional, e.g. "home_depot", "lowes")
- `sku`: string (optional, nullable) – product SKU where known
- `unit`: string (required, e.g. "piece", "ft")
- `notes`: text (optional)

### ProjectMaterial

Join table linking projects to default materials.

Fields (Django model: `ProjectMaterial`):
- `id`: PK
- `project`: FK → `Project`
- `material`: FK → `Material`
- `quantity`: numeric

### ShoppingList

Represents an actual working list for a user (can be based on a project).

Fields (Django model: `ShoppingList`):
- `id`: PK
- `user`: FK -> `User`
- `project`: FK → `Project` (nullable, for custom lists)
- `name`: string (e.g. "Copper pipe repair – Saturday")
- `created_at`: datetime

### ShoppingListItem

Join table linking materials to specific shopping lists (because a user can add or subtract materials from any shopping list).

Fields (Django model: `ShoppingListItem`):
- `id`: PK
- `shopping_list`: FK → `ShoppingList`
- `material`: FK → `Material`
- `quantity`: numeric 

### UserMaterial

Join table linking users to materials (to save information about which materials the user already has).

Fields (Django model: `UserMaterial`):
- `id`: PK
- `user`: FK → `User`
- `material`: FK → `Material`
- `quantity`: numeric 

---

## API design (Django REST, Phase 1)

We want clear, simple REST endpoints that React can call:

### Projects and their default materials

- `GET /api/projects/`
  - Returns a list of projects (id, name, description, url).
- `GET /api/projects/{id}/default-materials/`
  - Returns a list of default materials from `ProjectMaterial`.

### Users and materials they might already have

- `GET /api/user-materials/{user_id}/`
  - Returns a list of materials for that user
- `POST /api/user-materials/{user_id}/`
  - Request body includes required fields in `UserMaterial` (`user_id`, `material_id`, `quantity`)
    - Backend should: create a new `UserMaterial`
- `PATCH /api/user-materials/{user_id}/{material_id}/`
  - Edits the `quantity` that the user has
- `DELETE /api/user-materials/{user_id}/{material_id}/`
  - Deletes that UserMaterial

### Shopping lists

- `POST /api/shopping-lists/`
  - Create a new shopping list, optionally from a project template:
    - Request body can include `project_id` and `user_id`.
    - Backend should:
      - Create a `ShoppingList`.
      - Populate `ShoppingListItem` rows from that project’s `ProjectMaterial`s
- `GET /api/shopping-lists/user/{user_id}/`
  - Returns a list of shopping lists for that user (id, name, description, url).
- `GET /api/shopping-lists/{id}/`
  - Returns list details + items.
- `PATCH /api/shopping-lists/{id}/`
  - Update name

### Shopping list items

- `POST /api/shopping-lists/{id}/items/`
  - Adds a shopping list item (first creating a `Material` if the material doesn't already exist in the `Material` table)
    - Request body can include `quantity` and whatever required fields are in `Material` (like `name`, `category`, `unit`)
    - Backend should:
      - Create `ShoppingListItem` if it doesn't already exist
- `PATCH /api/shopping-list-items/{item_id}/`
  - Update quantity
- `DELETE /api/shopping-list-items/{item_id}/`
  - Remove an item.

---

## React UI requirements (Phase 1)

### Core views

1. **Project selection page**
   - Fetch `/api/projects/`.
   - Fetch `/api/shopping-lists/user/{user_id}/`.
   - Display as cards or list.
   - If the user already has a shopping list whose project_id matches that project, then display a button on the card titled 'Edit shopping list' -> call `GET /api/shopping-lists/{id}/` with `id=project_id` → navigate to shopping list page.
   - If the user doesn't already have a shopping list whose project id matches the project, then display a button on the card titled 'Start Project' → call `POST /api/shopping-lists/` with `project_id` → navigate to shopping list page.

2. **Shopping list page**
   - Fetch list & items via `/api/shopping-lists/{id}/`.
   - Fetch user material information via `/api/user-materials/{user_id}/`
     Cross-reference `UserMaterial`s with `ShoppingListItem`s to see if the user has the correct material and quantity already.
   - One section of the page will be called `Shopping List` and will list the items that the
     user does not already have. Each item will have an empty checkbox next to it, but if the 
     user clicks the checkmark -> call `POST /api/user-materials/{user_id}/` with the
     `material_id` and `quantity` specified in that `ShoppingListItem`
   - One section of the page will be called `Already Have` and will list the items that the
     user does have (also checking that the user has at least the quantity specified in `ShoppingListItem`). Each item will have an green checkmark next to it.
     - If the user clicks the checkmark 
        -> call `DELETE /api/user-materials/{user_id}/{material_id}/` with the `material_id` specified in that `ShoppingListItem`
     - If the user edits the quantity 
        -> call `PATCH /api/user-materials/{user_id}/{material_id}/` with the `material_id` specified in that `ShoppingListItem`
     - If the user clicks delete
        -> call `DELETE /api/user-materials/{user_id}/{material_id}/` with the `material_id` specified in that `ShoppingListItem`
   - One section of the page will allow:
     - Add new item with a form showing just required fields.
     - Delete item.

---

## Coding style & constraints

- Keep backend code idiomatic Django REST Framework:
  - Use serializers & viewsets or APIViews.
  - Use proper HTTP verbs (GET, POST, PATCH, DELETE).
- Keep frontend code idiomatic React:
  - Use functional components with hooks.
  - Clear separation between data fetching and UI where feasible.
- Focus on:
  - Clarity over cleverness.
  - Short, predictable API contracts (keep JSON fields stable).
- Avoid:
  - Over-engineering user auth for Phase 1.
  - Implementing Phase 2 logic in this context.

---

## Examples of what I want Copilot to help with

### Backend examples

- Implementing Django models for `Project`, `Material`, `ProjectMaterial`, `ShoppingList`, `ShoppingListItem`.
- Creating serializers and viewsets for:
  - Listing/creating shopping lists.
  - Listing/updating shopping list items.
- A view that takes `project_id` and creates a shopping list pre-populated from `ProjectMaterial`s.

### Frontend examples

- React component to:
  - Render projects from `/api/projects/`.
  - Create a shopping list and navigate to it.
- Shopping list component that:
  - Displays items with editable fields.
  - Sends PATCH/DELETE requests as user edits items.

---

## Non-goals for Copilot in this context

- Do not generate Phase 2 features (image upload, transition materials).
- Do not add complex authentication/authorization logic.
- Do not add Material deduplication logic
- Do not add payment or checkout logic beyond product links.

