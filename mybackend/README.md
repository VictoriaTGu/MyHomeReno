# DIY Project Planner - Backend

Django REST Framework API for the DIY Project Planner Phase 1 application.

## Prerequisites

- Python 3.8+
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
pip install django djangorestframework django-cors-headers
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
python manage.py runserver 0.0.0.0:8000
```

The API will be available at `http://localhost:8000`

## Project Structure

```
mybackend/
├── mybackend/           # Project settings
│   ├── settings.py     # Django settings (includes DRF, CORS)
│   ├── urls.py         # Main URL routing
│   └── wsgi.py
├── planner/            # Django app
│   ├── models.py       # Data models (Project, Material, etc.)
│   ├── serializers.py # DRF serializers
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

### Material
- `id`: Primary key
- `name`: Material/tool name
- `category`: Category (pipe, fitting, tool, etc.)
- `store`: Store hint (home_depot, lowes)
- `sku`: Product SKU
- `unit`: Unit of measurement (piece, ft, m)
- `notes`: Optional notes

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

### Projects
- `GET /api/projects/` - List all projects
- `GET /api/projects/{id}/` - Get project details
- `GET /api/projects/{id}/default-materials/` - Get project's default materials

### Materials
- `GET /api/materials/` - List all materials
- `GET /api/materials/{id}/` - Get material details

### Shopping Lists
- `GET /api/shopping-lists/` - List user's shopping lists
- `POST /api/shopping-lists/` - Create new shopping list
  - Body: `{ "name": "...", "project": id (optional), "user": id }`
- `GET /api/shopping-lists/{id}/` - Get shopping list with items
- `PATCH /api/shopping-lists/{id}/` - Update shopping list (e.g., name)

### Shopping List Items
- `POST /api/shopping-lists/{id}/items/` - Add item to list
  - Body: `{ "material": id }` or `{ "name": "...", "category": "...", "unit": "..." }`
- `PATCH /api/shopping-list-items/{item_id}/` - Update item quantity
- `DELETE /api/shopping-list-items/{item_id}/` - Remove item from list

### User Materials (Inventory)
- `GET /api/user-materials/{user_id}/` - List user's inventory
- `POST /api/user-materials/{user_id}/` - Add to user's inventory
- `PATCH /api/user-materials/{user_id}/{material_id}/` - Update inventory quantity

## Authentication

For Phase 1, all endpoints that modify data require basic Django user authentication. The frontend currently uses a mock user ID (1).

To test endpoints with authentication in production, include the user ID in requests.

## CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:5173` (React dev server)
- `http://localhost:3000` (alternative port)
- `http://127.0.0.1:5173`
- `http://127.0.0.1:3000`

## Notes

- User authentication is simplified for Phase 1 (mock user approach)
- Materials have unique constraint on (name, category, unit) to prevent duplicates
- Shopping list items are unique per list per material (can't add same material twice)
- User inventory tracks quantity of each material the user owns

## Next Steps

- Implement token-based authentication (JWT) for Phase 2
- Add image upload for projects
- Implement store integration/price lookup
- Add material search and filtering
