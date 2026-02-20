# Project: DIY Project Planner – Phase 4 (Per-Item Store Mapping & Checkout UX)

## High-level goal

Enhance the Shopping List experience so that **each ShoppingListItem** can:
1. On user click, show store + price details when its associated `Material` has store data.
2. Trigger a **store search flow** when it does not, reusing the Phase 2 store-search logic.
3. Show a **running total price + item count** for the entire `ShoppingList`.
4. Provide a fake “Checkout” paywall entry point (“Become a DIY Member to use Cart Checkout”).

Phase 4 is a **UI/UX + refactor** phase:
- Centralize the store search + material (updating `store`, `sku`, `product_title` and other product fields) logic so both the AddItem form and per-item flows share the same code.
- Keep the backend API shape consistent with Phase 2 (store search + material store mapping endpoints).

---

## Existing assumptions (from previous phases)

- `ShoppingListItem`:
  - `id`, `shopping_list` (FK), `material` (FK), `quantity`.
- `Material`:
  - `id`, `name`, `category`, `unit`, `notes`
  - Store mapping fields (primary/default store):
    - `store`: string (nullable, e.g. `"amazon"`, `"lowes"`, `"home_depot"`)
    - `sku`: string (nullable)
    - `product_title`: string (nullable)
    - `product_url`: string (nullable)
    - `product_image_url`: string (nullable)
    - Field to add: `price`: decimal (nullable, primary store price) – if not present, we will effectively treat `price` as part of the resolved product selection.

- Store search:
  - Backend exposes a search endpoint (Phase 2) which returns normalized `ProductResult` items:
    - `{ name, description, price, currency, sku, url, image_url, store }`

---

## New UX behaviors (Phase 4)

### 1. Clicking a ShoppingListItem

On the Shopping List page:

- Each item row becomes **clickable** (or has a “Details” button).
- When the user clicks an item:
  - **Case A – Material has store mapping (store & sku & price present)**  
    - Show a small details panel (popover or inline expansion) with:
      - Store name (e.g., “Amazon”, “Home Depot”).
      - Product title (from `material.product_title` or `material.name`).
      - Unit price.
      - Optional thumbnail and link to product page.
  - **Case B – Material lacks store mapping (store/sku/price null)**  
    - Show a panel with:
      - Basic material info (`material.name`, `quantity`, `unit`).
      - A **“Search Stores”** button.

---

## Detailed behavior: “Search Stores” flow

### Trigger

- When a ShoppingListItem’s detail panel detects `material.store`, `material.sku`, or `material.price` is missing, it renders the **“Search Stores”** button.

### API request

Click “Search Stores” → call:

- `POST /api/store-search/search/`

**Request body (JSON):**

```json
{
  "query": "<derived query from the material name>",
  "store": "home_default",     // or default store (configurable)
  "limit": 5
}
```

### Displaying search results
    - Show a modal or inline panel listing the top 5 results:
    - Each item row:
        - Thumbnail image.
        - Product name.
        - Short description.
        - Price & currency.
        - “Select” button.

### If the user clicks "Select" on one of the top 5 search results:
- Make a call to update the Material:
- Material mapping endpoint:
  - `PATCH /api/materials/{material_id}/store-mapping/`
    - Updates `store`, `sku`, `product_title`, `product_url`, `product_image_url`, and `price`.

**Request body (JSON):**

```json
{
  "store": "amazon",
  "sku": "B00COPPER123",
  "product_title": "1/2\" Copper Pipe, 10 ft",
  "product_url": "https://www.amazon.com/dp/B00COPPER123",
  "product_image_url": "https://images.amazon.com/small/B00COPPER123.jpg",
  "price": 24.99,
  "unit": "piece"  // or "ft", depending on how you use unit
}
```

### Backend:
- Updates the Material with this store mapping.

### Frontend:
- Closes the search modal.
- Re-renders the item detail panel, now in Case A (store mapping present), showing store & price.

### If the user does not select any of the top 5:
- Close the search modal without calling the PATCH endpoint.
- Material remains without store mapping.
- Detail panel continues to show only the basic info and the “Search Stores” button.

### Important:

- The search + selection logic should be centralized in a reusable component/hook so that:
- The AddItemForm (Phase 2) can use it.
- The ShoppingListItem details (Phase 4) can use it.
- We avoid duplicating store search + material mapping logic.

## Detailed behavior: New aggregate info at bottom of Shopping List
At the bottom of the Shopping List page, show:
- Total price
- Total number of items

### Computation rules
- Total number of items: Sum of quantity across all ShoppingListItems
- Total price:
    - For each ShoppingListItem:
        - If material.price is set: Add material.price * item.quantity.
        - Else:
        - Skip or treat as 0 (explicitly choose behavior).

## Detailed behavior: Fake “Checkout” paywall button
- At the bottom of the Shopping List page, below the total: Show a “Checkout” button.

### Trigger:

- Clicking “Checkout” opens a fake paywall pop-up (modal) with text like: “Become a DIY Member to use Cart Checkout”
- Optional CTA buttons:
    - “Learn more” → navigates to a pricing/coming-soon page.
    - “Close” → dismisses modal.