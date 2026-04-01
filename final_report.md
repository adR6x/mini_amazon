# Mini Amazon
## Final Project Report

**Course:** CS 516 - Database Systems, Duke University  
**Repository:** [github.com/adR6x/mini_amazon](https://github.com/adR6x/mini_amazon)

Mini Amazon is a full-stack e-commerce platform built for Duke's CS 516 final project. It models a realistic online marketplace in which the same user can act as both buyer and seller. The project centers on relational schema design, transactional checkout, database-driven business rules, and efficient product search in PostgreSQL.

### Technology Stack
- **Backend:** Python 3, Flask
- **Database:** PostgreSQL
- **Query Layer:** SQLAlchemy with thin raw-SQL wrappers
- **Frontend:** Jinja2 templates, Bootstrap 5
- **Authentication:** Flask-Login and Werkzeug password hashing

### Team Contributors
- **Anubhav Dhakal (`ad641`)** - Full-stack development; major work on buyer-side UI, products, cart, reviews, and security
- **Da Lin (`dl402`)** - Inventory management and seller dashboard
- **Jun Yang** - Orders, fulfillment flow, and revenue trends
- **Mirsaid Ravilov (`mr563`)** - Cart, checkout, and coupons
- **Tianze Ren (`tr158`)** - Order fulfillment
- **Malika Syzdykova (`ms1254`)** - User profiles and seller reviews

> The original course skeleton was created by Rickard Stureborg and Yihao Hu and later updated by course staff.

### Database Design
The PostgreSQL database contains **12 tables** that cover the complete marketplace workflow:

- **User and catalog data:** `Users`, `Categories`, `Products`, `Inventory`
- **Shopping flow:** `Carts`, `Cart_Items`, `Orders`, `Order_Items`, `Coupons`
- **Feedback and engagement:** `Product_Reviews`, `Seller_Reviews`, `Product_Review_Upvotes`

Key design choices:

- **Single `Users` table:** buyers and sellers share one identity model, which reduces duplication and simplifies joins
- **`Inventory` as a seller-product bridge:** multiple sellers can offer the same product with different prices and stock levels
- **One-cart-per-user rule:** enforced with a unique constraint on `Carts.user_id`
- **Review integrity:** one product review per `(reviewer_id, product_id)` and one seller review per `(reviewer_id, seller_id)`
- **Coupon integrity:** discount codes are globally unique
- **Upvote cleanup:** product review upvotes cascade on delete so dependent rows are removed automatically

The schema also uses two triggers to keep pricing synchronized:

- **`update_products_price_trigger`:** when an inventory price changes, the corresponding `Products.price` is updated
- **`update_cart_items_price_trigger`:** when a product price changes, related `Cart_Items.unit_price` values are refreshed

### Core Features
- **Authentication and profiles:** secure registration/login, editable user profiles, wallet balance updates, and public seller pages with ratings and review history
- **Product discovery:** paginated browsing plus filtering by category, price, and minimum rating
- **Fuzzy search:** PostgreSQL `pg_trgm` similarity search across product, seller, and category fields for typo-tolerant results
- **Cart workflow:** users can add items, update quantities, remove items, or save products for later
- **Transactional checkout:** order creation, inventory decrement, buyer debit, seller credit, and order-item insertion all happen in one transaction
- **Coupon support:** seller-issued coupons apply discounts at checkout and are capped by each seller's subtotal
- **Order management:** buyers can view order history; sellers can fulfill line items and automatically update overall order status
- **Inventory tools:** sellers can create listings, edit product details, adjust stock, and filter inventory by keyword or metadata
- **Review system:** buyers can create, edit, and delete product and seller reviews; product reviews also support upvotes
- **Analytics:** sellers can view revenue trends over time

### Security and Reliability
- Parameterized queries are used throughout to prevent SQL injection
- Input validation covers email format, field lengths, and general sanitization
- Security headers include `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, and a Content Security Policy
- Request logging captures HTTP method, URL, and remote IP for debugging and monitoring

### Application Structure
- **Routes:** `app/users.py`, `app/product.py`, `app/cart.py`, `app/review.py`, `app/inventory_routes.py`
- **Models:** separate modules for users, products, carts, inventory, purchases, and reviews under `app/models/`
- **Database scripts:** schema and sample-data setup live in `db/create.sql`, `db/load.sql`, and `db/setup.sh`
- **Entry point:** `amazon.py`

### Key Design Decisions
- **Dual-role users:** treating buyers and sellers as the same entity makes the system easier to extend and keeps user data centralized
- **Bridge-based inventory:** inventory is modeled independently from products so seller-specific pricing and stock are preserved cleanly
- **Atomic checkout:** wrapping checkout in one database transaction prevents partial orders and inconsistent balances
- **Snapshot pricing with synchronization:** cart items store a price snapshot, while triggers keep those values aligned with later listing changes
- **Database-powered search:** trigram similarity produces stronger search quality than plain keyword matching for a marketplace UI
