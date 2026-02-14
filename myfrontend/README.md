# DIY Project Planner - Frontend

React frontend for the DIY Project Planner Phase 1 application.

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm 9+ or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file (copy from `.env.example`) and configure the API base URL:
```bash
cp .env.example .env
```

3. Update `.env` if needed (default is `http://localhost:8000`):
```
VITE_API_BASE_URL=http://localhost:8000
```

### Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build

Build for production:
```bash
npm run build
```

### Preview

Preview the production build locally:
```bash
npm run preview
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ProjectSelection.jsx
│   ├── ShoppingList.jsx
│   ├── ShoppingListItem.jsx
│   └── AddItemForm.jsx
├── pages/              # Page components (routes)
│   ├── ProjectSelectionPage.jsx
│   └── ShoppingListPage.jsx
├── services/           # API and utilities
│   ├── api.js         # Axios API client and endpoints
│   └── constants.js   # API configuration
├── App.jsx            # Main app with routing
├── App.css
├── main.jsx           # Entry point
└── index.css          # Global styles
```

## Features

### Phase 1

- ✅ Project selection from predefined templates
- ✅ Create shopping lists from project templates
- ✅ View and edit shopping list items
- ✅ Track quantities and material details
- ✅ Add new items to shopping lists
- ✅ Delete items from lists
- ✅ Cross-reference user inventory

## API Integration

The frontend communicates with the Django REST Framework backend at `http://localhost:8000`.

Key endpoints used:
- `GET /api/projects/` - List all projects
- `POST /api/shopping-lists/` - Create a new shopping list
- `GET /api/shopping-lists/{id}/` - Get shopping list details
- `POST /api/shopping-lists/{id}/items/` - Add item to list
- `PATCH /api/shopping-list-items/{item_id}/` - Update item
- `DELETE /api/shopping-list-items/{item_id}/` - Delete item
- `GET /api/user-materials/{user_id}/` - Get user's inventory

## Notes

- User authentication is mocked (using user_id = 1) for Phase 1
- The backend must be running on `localhost:8000` for the dev server to work properly
- API requests are proxied through Vite dev server to avoid CORS issues

## Next Steps

- Set up the Django backend
- Seed initial project and material data
- Test the full application flow
