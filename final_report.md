# Mini Amazon — Final Project Report

**Course:** CS 516 — Database Systems, Duke University  
**Repository:** [github.com/adR6x/mini_amazon](https://github.com/adR6x/mini_amazon)

---

## Overview

Mini Amazon is a full-stack e-commerce web application modeled after Amazon, built as the final project for CS 516 (Database Systems) at Duke University. The application supports multi-role interactions — users can browse products as customers, list and manage products as sellers, and leave reviews for both products and sellers. The project emphasizes relational database design, transactional integrity, and query optimization using PostgreSQL.

**Technology Stack**
- **Backend:** Python 3, Flask
- **Database:** PostgreSQL
- **ORM/Query Layer:** SQLAlchemy (raw SQL via a thin db wrapper)
- **Frontend:** Jinja2 templates, Bootstrap 5
- **Auth:** Flask-Login, Werkzeug password hashing (bcrypt)

---

## Team Contributors

| Name | GitHub / NetID | Role |
|---|---|---|
| Anubhav Dhakal | adR6 / ad641 | Full-stack (top contributor — products, reviews, security, cart) |
| Da Lin | dl402 | Inventory management, seller dashboard |
| Jun Yang | — | Orders, fulfillment, revenue trends |
| Mirsaid Ravilov | mr563 | Cart, checkout, coupons |
| Tianze Ren | tr158 | Order fulfillment, UI improvements |
| Malika Syzdykova | ms1254 | User profiles, seller reviews |

> The project skeleton was originally created by Rickard Stureborg and Yihao Hu for the Fall 2021 semester and has been amended by course staff in subsequent years.

---

## Database Schema

The application uses a PostgreSQL database (`amazon`) with 12 tables designed to capture the full lifecycle of an e-commerce platform.

### Entity-Relationship Summary

```
Users ──< Products (seller_id)
Users ──< Carts (user_id)
Carts ──< Cart_Items >── Products
Cart_Items >── Users (seller_id)
Users ──< Orders (buyer_id)
Orders ──< Order_Items >── Products
Order_Items >── Users (seller_id)
Products >── Categories
Products ──< Inventory >── Users (seller_id)
Products ──< Product_Reviews >── Users (reviewer_id)
Users ──< Seller_Reviews >── Users (reviewer_id / seller_id)
Users ──< Coupons (seller_id)
Product_Reviews ──< Product_Review_Upvotes >── Users
```

### Table Descriptions

#### `Users`
Central identity table. Every actor (buyer, seller, or both) is a `User`.

| Column | Type | Notes |
|---|---|---|
| id | INT (PK, identity) | Auto-generated primary key |
| email | VARCHAR (UNIQUE) | Login credential |
| password | VARCHAR(255) | bcrypt hashed |
| firstname / lastname | VARCHAR(255) | Display name |
| address | VARCHAR(255) | Shipping address |
| balance | NUMERIC(10,2) | Wallet balance — used for purchases |

#### `Categories`
Flat product category taxonomy.

| Column | Type | Notes |
|---|---|---|
| category_id | INT (PK) | |
| name | VARCHAR(255) | Category label |
| description | TEXT | Optional description |

#### `Products`
Listings created by sellers. Each product belongs to one seller and one category.

| Column | Type | Notes |
|---|---|---|
| product_id | INT (PK) | |
| seller_id | INT (FK → Users) | The seller who listed this product |
| category_id | INT (FK → Categories) | |
| name | VARCHAR(255) | |
| description | TEXT | |
| image_url | TEXT | |
| price | DECIMAL(12,2) | Must be ≥ 0 |

#### `Carts` and `Cart_Items`
Each user has at most one cart (enforced by a UNIQUE constraint on `user_id`). Cart items support a "save for later" workflow.

**Cart_Items notable columns:**
- `status`: `in_cart` or `saved_for_later`
- `unit_price`: snapshot of the price at the time of adding
- `seller_id`: tracks which seller's inventory to decrement at checkout

#### `Orders` and `Order_Items`
Created atomically during checkout. An order has a top-level `fulfillment_status` (`pending`, `partial`, `fulfilled`) that is recomputed whenever a seller marks one of its items fulfilled.

**Order_Items notable columns:**
- `fulfillment_status`: per-item status (`pending` or `fulfilled`)
- `fulfilled_at`: timestamp set when the item is fulfilled

#### `Inventory`
A separate table that tracks how many units each seller has available for each product, along with the seller-specific price. A unique constraint on `(seller_id, product_id)` ensures no duplicate entries.

#### `Product_Reviews`
Buyers can leave one review per product (enforced by `UNIQUE (reviewer_id, product_id)`). Supports 1–5 star ratings, text, and an optional image.

#### `Seller_Reviews`
Buyers can leave one review per seller (enforced by `UNIQUE (reviewer_id, seller_id)`). Same structure as product reviews.

#### `Product_Review_Upvotes`
Tracks which users have upvoted which product reviews. Composite primary key `(review_id, user_id)` prevents duplicate votes. Cascades on delete so upvotes are cleaned up if a review is removed.

#### `Coupons`
Sellers can create discount codes with a fixed monetary value and an expiration date. Codes are globally unique (`UNIQUE (code)`).

---

## Database Triggers

Two PostgreSQL triggers maintain price consistency across tables:

1. **`update_products_price_trigger`** — When a seller updates the price in `Inventory`, the corresponding `Products.price` is automatically updated.
2. **`update_cart_items_price_trigger`** — When `Products.price` changes, all `Cart_Items` referencing that product have their `unit_price` updated to reflect the new price.

This ensures that cart prices always reflect the current listed price without requiring application-level synchronization.

---

## Features Implemented

### Authentication & User Management
- Secure registration and login using bcrypt password hashing
- Profile editing: name, email, password, shipping address, wallet balance top-up
- Public seller profile pages showing seller stats (total products, total sales, average rating) and reviews

### Product Browsing & Search
- Browse all products with pagination
- Filter by category, price range, and minimum rating
- Full-text fuzzy search using PostgreSQL's `pg_trgm` extension — searches across product name, description, seller name, seller address, and category name, ranked by trigram similarity

### Cart & Checkout
- Add items to cart (automatically creates a cart if one doesn't exist)
- Update quantities, remove items, or save items for later
- Checkout validates inventory availability and buyer wallet balance before committing
- Checkout is executed in a single database transaction: creates the order, inserts order items, decrements inventory, credits each seller's balance, and debits the buyer's balance atomically
- Coupon code support: sellers can issue discount codes; discounts are applied at checkout and capped at the seller's subtotal

### Order Management
- **Buyer view:** order history with filters (status, date range) and pagination
- **Seller view:** incoming orders for their products, with the ability to mark individual items as `fulfilled`; the parent order's status updates automatically (`pending` → `partial` → `fulfilled`)

### Inventory Management (Sellers)
- Add new products and set initial inventory quantities and prices
- Edit product details (name, description, image, category, price, quantity)
- Delete products from inventory
- Filter and sort inventory by price, quantity, category, or keyword search

### Reviews
- **Product reviews:** create, edit, delete; one review per buyer per product
- **Seller reviews:** create, edit, delete; one review per buyer per seller
- Upvote/remove upvote on product reviews
- Review history pages for users showing all their reviews

### Seller Analytics
- Revenue trends dashboard showing sales data over time

### Security
- SQL injection prevention via parameterized queries throughout
- Input sanitization and pattern validation (email format, length limits)
- HTTP security headers on every response: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, and a Content Security Policy
- All requests are logged with method, URL, and remote IP

---

## Application Structure

```
mini_amazon/
├── app/
│   ├── models/              # Database model classes (one per entity)
│   │   ├── user.py
│   │   ├── product.py       # Product + Category + Inventory (detail view)
│   │   ├── carts.py         # Cart, CartItem, checkout logic
│   │   ├── inventory.py     # Seller inventory CRUD
│   │   ├── product_review.py
│   │   ├── seller_review.py
│   │   ├── purchase.py      # Order history & seller order queries
│   │   └── wishlist.py
│   ├── templates/           # Jinja2 HTML templates
│   ├── users.py             # Auth, profile, order, coupon routes
│   ├── product.py           # Product browsing & detail routes
│   ├── cart.py              # Cart & checkout routes
│   ├── review.py            # Product & seller review routes
│   ├── inventory_routes.py  # Seller inventory routes
│   ├── wishlist.py          # Wishlist routes
│   └── security.py          # SecurityValidation, SQLInjectionPrevention, middleware
├── db/
│   ├── create.sql           # Schema definition
│   ├── load.sql             # Sample data loader
│   ├── setup.sh             # Database initialization script
│   └── data/                # CSV seed data
└── amazon.py                # Flask app entry point
```

---

## Key Design Decisions

**Dual-role users:** Rather than separate `Buyer` and `Seller` tables, a single `Users` table handles both roles. A user is treated as a seller if they have entries in `Inventory`. This simplifies joins and avoids data duplication.

**Inventory as a bridge table:** The `Inventory` table acts as a many-to-many bridge between sellers and products, allowing multiple sellers to offer the same product at different prices and quantities.

**Transactional checkout:** The entire checkout process runs inside a single `BEGIN`/`COMMIT` block, ensuring that partial failures (e.g., insufficient stock discovered mid-checkout) do not leave the database in an inconsistent state.

**Snapshot pricing:** `Cart_Items.unit_price` captures the price at the time of adding to cart, while database triggers keep it synchronized with live price changes — matching the behavior of real e-commerce platforms.

**Fuzzy search with pg_trgm:** Rather than simple `ILIKE` matching, the search feature uses PostgreSQL's trigram similarity scoring to return relevant results even for partial or misspelled queries, ranked by relevance.
