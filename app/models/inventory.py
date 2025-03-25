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
