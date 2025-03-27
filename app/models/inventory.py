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
        print(seller_id)
        rows = app.db.execute("""
            SELECT i.seller_id, i.product_id, p.name, i.quantity_available, i.price
            FROM Inventory i
            JOIN Products p ON i.product_id = p.product_id
            WHERE i.seller_id = :seller_id
        """, seller_id=seller_id)
        print(rows)

        return [Inventory(*row) for row in rows] if rows else []

    @staticmethod
    def update_field(seller_id, product_id, field, value):
        if field not in {"quantity_available", "price"}:
            raise ValueError("Invalid field")

        result = app.db.execute(f"""
            UPDATE Inventory
            SET {field} = :value
            WHERE product_id = :product_id AND seller_id = :seller_id
            RETURNING product_id
        """, value=value, product_id=product_id, seller_id=seller_id)

        return result