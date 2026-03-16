# DIY Project Planner

React / Django / LLM DIY Project Planner.

## Prerequisites

- Python 3.12
- Virtual environment setup

## Setup

### 1. Activate Virtual Environment

```bash
source ../.venv/bin/activate  # macOS/Linux
# or
..\.venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Seed Test Data

```bash
python manage.py seed_data
```

This creates:
- Test user: `testuser` / password: `testpass123`
- 13 sample materials (pipes, fittings, tools, fixtures)
- 3 sample projects with associated materials

### 5. Start Development Server

```bash
export DEBUG=True
export STORE_SEARCH_USE_DUMMY=False
python manage.py runserver 0.0.0.0:8000
```

The app will be available at `http://localhost:5173`

## Project Structure

```
mybackend/
├── mybackend/          # Project settings
│   ├── settings.py     # Django settings (includes DRF, CORS)
│   ├── urls.py         # Main URL routing
│   └── wsgi.py
├── planner/            # Django app
│   ├── models.py       # Data models (Project, Material, etc.)
│   ├── serializers.py  # DRF serializers
│   ├── views.py        # ViewSets for API endpoints
│   ├── urls.py         # App URL routing
│   ├── migrations/     # Database migrations
│   └── management/
│       └── commands/
│           └── seed_data.py  # Management command for seeding data
└── manage.py
```

## Models

### Project
- `id`: Primary key
- `name`: Project name
- `description`: Optional project description
- `img`: Optional image URL
- `steps`: AI-generated project steps (JSON list) - nullable (Phase 3+)

### Material
- `id`: Primary key
- `name`: Material/tool name
- `category`: Category (pipe, fitting, tool, etc.)
- `store`: Primary store (home_depot, lowes, amazon, etc.) - nullable
- `sku`: Product SKU (ASIN for Amazon, etc.) - nullable
- `unit`: Unit of measurement (piece, ft, m)
- `notes`: Optional notes
- `product_title`: Product name from store - nullable (Phase 2+)
- `product_url`: Direct product link - nullable (Phase 2+)
- `product_image_url`: Product image URL - nullable (Phase 2+)
- `price`: Product price (decimal, 10 digits, 2 decimals) - nullable 

### ProjectMaterial
Join table linking projects to default materials.
- `project`: FK to Project
- `material`: FK to Material
- `quantity`: Quantity needed

### ShoppingList
- `user`: FK to User
- `project`: Optional FK to Project (can be null for custom lists)
- `name`: List name
- `created_at`: Creation timestamp

### ShoppingListItem
Join table for shopping list items.
- `shopping_list`: FK to ShoppingList
- `material`: FK to Material
- `quantity`: Quantity in this list

### UserMaterial
User's inventory of materials they already own.
- `user`: FK to User
- `material`: FK to Material
- `quantity`: Quantity they have

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Token-based login
  - Body: `{ "username": "...", "password": "..." }`
  - Response: `{ "token": "...", "user_id": 1 }`

### Projects
- `GET /api/projects/` - List all projects
- `POST /api/projects/` - Create project with default materials
  - Body: `{ "name": "...", "description": "...", "img": "...", "steps": [...], "materials": [...] }`
- `GET /api/projects/{id}/` - Get project details
- `GET /api/projects/{id}/default-materials/` - Get project's default materials (custom action)
- `POST /api/projects/{id}/default-materials/` - Add default materials to project (custom action)

### Materials
- `GET /api/materials/` - List all materials
- `GET /api/materials/{id}/` - Get material details
- `PATCH /api/materials/{id}/store-mapping/` - Update material's store product mapping (Phase 2+)
  - Body: `{ "store": "amazon", "sku": "...", "product_title": "...", "product_url": "...", "product_image_url": "...", "price": 12.99 }`

### Shopping Lists
- `GET /api/shopping-lists/` - List current user's shopping lists
- `GET /api/shopping-lists/user/` - Get shopping lists for a specific user (custom action)
  - Query param: `user_id` (required)
- `POST /api/shopping-lists/` - Create new shopping list
  - Body: `{ "name": "...", "project": id (optional) }`
- `GET /api/shopping-lists/{id}/` - Get shopping list with items
- `PATCH /api/shopping-lists/{id}/` - Update shopping list (e.g., name)

### Shopping List Items
- `POST /api/shopping-lists/{shopping_list_id}/items/` - Add item to list
  - Body (with existing material): `{ "material": id, "quantity": 5 }`
  - Body (with auto-creation): `{ "name": "...", "category": "...", "unit": "...", "quantity": 5, "product_selection": {...} }`
- `GET /api/shopping-list-items/{item_id}/` - Get item details
- `PATCH /api/shopping-list-items/{item_id}/` - Update item quantity
  - Body: `{ "quantity": 10 }`
- `DELETE /api/shopping-list-items/{item_id}/` - Remove item from list

### Product Search (Phase 2+)
- `GET /api/store-search/search/` - Search for products (custom action)
  - Query params:
    - `q` (required): Search query string
    - `store` (optional): Store name (default: `home_depot`)
    - `limit` (optional): Max number of results (default: 5)
  - Response: List of normalized `ProductResult` objects with `name`, `description`, `price`, `currency`, `sku`, `url`, `image_url`, `store`

### User Materials (Inventory)
- `GET /api/user-materials/{user_id}/` - List user's inventory
- `POST /api/user-materials/{user_id}/` - Add to user's inventory
  - Body (with existing material): `{ "material": id, "quantity": 5 }`
  - Body (with auto-creation): `{ "name": "...", "category": "...", "unit": "...", "quantity": 5 }`
- `GET /api/user-materials/{user_id}/{material_id}/` - Get user's inventory for a specific material
- `PATCH /api/user-materials/{user_id}/{material_id}/` - Update inventory quantity
  - Body: `{ "quantity": 10 }`
- `DELETE /api/user-materials/{user_id}/{material_id}/` - Remove item from inventory

### Plan Generation (Phase 3+)
- `POST /api/generate-plan/` - Generate AI-powered project plan from free-form description
  - Body: `{ "description": "replace ½ inch copper pipe leaking under kitchen sink..." }`
  - Response: `{ "materials": [...], "tools": [...], "steps": [...], "warnings": [...] }`

## Notes

- Materials have unique constraint on (name, category, unit) to prevent duplicates
- Shopping list items are unique per list per material (can't add same material twice)
- User inventory tracks quantity of each material the user owns

## Implementation Phases

### Phase 1: Core Shopping Lists (Complete)
- Basic project and material templates
- Shopping list creation and management
- Shopping list items (add/update/remove materials)
- Token-based authentication
- User inventory tracking

### Phase 2: Dynamic Product Search & Selection (Complete)
- Free-form material search using external APIs (SerpAPI for Home Depot, Amazon, etc.)
- Product selection UI with top 5 results
- Material store mapping (save store, SKU, product title, URL, image, price)
- Store search abstraction layer for multi-store support
- Material auto-creation when adding items to shopping lists
- Optional product selection during item addition

### Phase 3: AI-Powered Project Planning (In Progress)
- Free-form project description input
- RAG (Retrieval-Augmented Generation) pipeline using OpenAI + ChromaDB
- Structured plan generation (materials, tools, steps, warnings)
- Project creation from AI-generated plans
- ChromaDB vector store for persistent knowledge base

### Phase 4: Per-Item Store Mapping & Checkout UX (Planned)
- Click to see item details with store info
- "Search Stores" button for items without product mapping
- Running total price and item count
- Fake checkout paywall for premium features
- Centralized store search component for reuse
