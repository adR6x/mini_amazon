from flask import current_app as app

class Inventory:
    def __init__(self, seller_id, product_id, product_name, quantity_available, price):
        self.seller_id = seller_id
        self.product_id = product_id
        self.product_name = product_name
        self.quantity_available = quantity_available
        self.price = price

    @staticmethod
    def get_by_seller(seller_id):
        rows = app.db.execute("""
            SELECT i.seller_id, i.product_id, p.name AS product_name, i.quantity_available, i.price
            FROM Inventory i
            JOIN Products p ON i.product_id = p.product_id
            WHERE i.seller_id = :seller_id
        """, seller_id=seller_id)

        return [Inventory(*row) for row in rows] if rows else []

    @staticmethod
    def get_inventory_detail(product_id):
        rows = app.db.execute('''
            SELECT i.seller_id, i.product_id, p.name AS product_name, p.description, p.image_url, p.category_id, i.quantity_available, i.price
            FROM Inventory i
            JOIN Products p ON i.product_id = p.product_id
            WHERE i.product_id = :product_id
        ''', product_id=product_id)

        return rows[0] if rows else None

    @staticmethod
    def update_field(seller_id, product_id, field, value):
        # Define valid fields for each table
        inventory_fields = {"quantity_available", "price"}
        product_fields = {"product_name", "description", "image_url", "category_id"}

        # Determine which table to update
        if field in inventory_fields:
            table = "Inventory"
        elif field in product_fields:
            table = "Products"
        else:
            raise ValueError("Invalid field")

        # Map field names to database column names if necessary
        field_mapping = {
            "product_name": "name",
            "description": "description",
            "image_url": "image_url",
            "category_id": "category_id",
            "quantity_available": "quantity_available",
            "price": "price"
        }

        # Execute the update query
        result = app.db.execute(f"""
            UPDATE {table}
            SET {field_mapping[field]} = :value
            WHERE product_id = :product_id AND seller_id = :seller_id
            RETURNING product_id
        """, value=value, product_id=product_id, seller_id=seller_id)

        return result

    @staticmethod
    def product_exists(seller_id, product_name):
        rows = app.db.execute('''
            SELECT 1
            FROM Products
            WHERE seller_id = :seller_id AND name = :product_name
        ''', seller_id=seller_id, product_name=product_name)
        return len(rows) > 0

    @staticmethod
    def add_product(seller_id, category_id, short_name, description, image_url, price):
        rows = app.db.execute('''
            INSERT INTO Products (seller_id, category_id, name, description, image_url, price)
            VALUES (:seller_id, :category_id, :short_name, :description, :image_url, :price)
            RETURNING product_id
        ''', seller_id=seller_id, category_id=category_id, short_name=short_name, description=description, image_url=image_url, price=price)
        return rows[0][0] if rows else None

    @staticmethod
    def add_inventory(seller_id, product_id, quantity_available, price):
        rows = app.db.execute('''
            INSERT INTO Inventory (seller_id, product_id, quantity_available, price)
            VALUES (:seller_id, :product_id, :quantity_available, :price)
            RETURNING id
        ''', seller_id=seller_id, product_id=product_id, quantity_available=quantity_available, price=price)
        return rows[0][0] if rows else None

    @staticmethod
    def get_all_categories():
        rows = app.db.execute('''
            SELECT category_id, name
            FROM Categories
        ''')
        return [{'id': row[0], 'name': row[1]} for row in rows] if rows else []

    @staticmethod
    def get_inventory_items(page, items_per_page):
        offset = (page - 1) * items_per_page
        rows = app.db.execute('''
            SELECT i.seller_id, i.product_id, p.name, i.quantity_available, i.price
            FROM Inventory i
            JOIN Products p ON i.product_id = p.product_id
            LIMIT :items_per_page OFFSET :offset
        ''', items_per_page=items_per_page, offset=offset)
        return [Inventory(*row) for row in rows] if rows else []

    @staticmethod
    def get_total_inventory_count():
        result = app.db.execute('SELECT COUNT(*) FROM Inventory')
        return result[0][0] if result else 0