from flask import current_app as app

class Product:
    def __init__(self, id, name, price, description=None, image_url=None, seller_id=None, category_id=None):
        self.id = id
        self.name = name
        self.price = price
        self.description = description
        self.image_url = image_url
        self.seller_id = seller_id
        self.category_id = category_id

    @staticmethod
    def get(id):
        rows = app.db.execute('''
            SELECT product_id AS id, name, price, description, image_url, seller_id, category_id
            FROM Products
            WHERE product_id = :id
        ''', id=id)
        return Product(*rows[0]) if rows else None

    @staticmethod
    def get_all():
        rows = app.db.execute('''
            SELECT product_id AS id, name, price, description, image_url, seller_id, category_id
            FROM Products
        ''')
        return [Product(*row) for row in rows]
