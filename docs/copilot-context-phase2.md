# Project: DIY Project Planner – Phase 2 (Dynamic Product Search & Selection)

## High-level goal

Extend the DIY Project Planner to support **dynamic product search and selection** when a user adds a `ShoppingListItem` using free‑form text for the material name.

For Phase 2, when the user adds an item to a shopping list:

1. The user **enters a free‑form material name** (e.g., `"1/2 inch copper pipe"`) and quantity in a form on the Shopping List page.
2. The backend uses that free‑form name as the **search query** to an external product API (initially the Amazon Product API, later swappable for Lowe’s, Home Depot, etc.).
3. The UI displays the **top 5 product matches** with:
   - Product image
   - Title/name
   - Short description and price
   - A “more details” pop‑up when the user clicks a result
4. The user can:
   - Choose one product → the chosen product’s store mapping is saved onto the corresponding `Material` (using its `store`, `sku`, and new product fields), and a `ShoppingListItem` is created pointing to that `Material`.
   - Or skip selection → a `Material` and `ShoppingListItem` are still created, but `Material.store`, `Material.sku`, and related product fields remain `null`.

Phase 2 focuses on:

- Using free‑form item names to drive product search.
- Updating the **Material** record with primary store mapping when a product is chosen (Option A).
- Keeping `ShoppingListItem` unchanged as a simple link between `ShoppingList` and `Material`.

This file should be read together with `copilot-context-phase1.md`, which defines the base models and Phase 1 behavior.

---

## Tech stack (unchanged)

- Frontend: React with a simple component hierarchy.
- Backend: Django REST Framework (Python).
- Database: PostgreSQL on local dev.

New in Phase 2:

- External product APIs:
  - Initial implementation: **Amazon Product API** (or a mocked equivalent) for search.
  - Later: Alternates (Lowe’s, Home Depot, etc.) hidden behind a store‑agnostic abstraction.

---

## Data model (Phase 2 additions, Option A)

Phase 1 models stay as‑is, except we enrich `Material` to hold the **primary/default store mapping**. `ShoppingListItem` remains unchanged and always links to `Material` only.

### Material (extended for store product mapping)

Phase 1 fields (for reference):

- `id`: PK  
- `name`: string (required, e.g. `"1/2\" copper pipe"`, `"pipe cutter"`)  
- `category`: string (required, e.g. `"fitting"`, `"tool"`)  
- `store`: string (optional, e.g. `"home_depot"`, `"lowes"`)  
- `sku`: string (optional, nullable) – product SKU where known  
- `unit`: string (required, e.g. `"piece"`, `"ft"`)  
- `notes`: text (optional)  

Phase 2 extends the meaning of some fields and adds a few more:

- `store`: string (nullable)  
  - Now treated as the **primary/default store** for this material (e.g., `"amazon"`, `"lowes"`, `"home_depot"`).
- `sku`: string (nullable)  
  - Store‑specific product identifier for the primary store:
    - Amazon: ASIN
    - Lowe’s: product ID / SKU ID
    - Home Depot: store SKU number
- `product_title`: string (nullable)  
  - The product title as shown on the store’s site.
- `product_url`: string (nullable)  
  - Deep link to the product page on the store’s site.
- `product_image_url`: string (nullable)  
  - Main product image URL from the store.

Key rule:

- If the user picks a product from the search results:
  - `store`, `sku`, `product_title`, `product_url`, `product_image_url` on the associated `Material` should be updated to match the chosen product.
- If the user does **not** pick a product:
  - Those fields remain `null` (or unchanged).

### ShoppingListItem (unchanged)

Phase 1 structure remains:

- `id`: PK  
- `shopping_list`: FK → `ShoppingList`  
- `material`: FK → `Material`  
- `quantity`: numeric  

You may optionally add a `label`/`display_name` field if you want per‑item override text, but **Phase 2 does not require any structural changes** to `ShoppingListItem`.

---

## Product search abstraction layer

We do not want the React frontend to know about Amazon vs Lowe’s vs Home Depot. The backend exposes a single, simple API and uses an internal abstraction to talk to different providers.

### Internal Python interface

Define types for a normalized product result:

```python
from typing import Protocol, List, TypedDict

class ProductResult(TypedDict):
    name: str
    description: str
    price: float
    currency: str
    sku: str
    url: str
    image_url: str
    store: str  # e.g. "amazon", "lowes", "home_depot"

class StoreSearchClient(Protocol):
    def search_products(self, query: str, *, limit: int = 5) -> List[ProductResult]:
```
