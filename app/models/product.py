from flask import current_app as app

class Product:
    def __init__(self, id, name, price, description=None, image_url=None, seller_id=None, category_id=None):
        self.id = id
        self.name = name
        self.description = description
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

    @staticmethod
    def get_all_top5(available=True):
        rows = app.db.execute('''
SELECT product_id AS id, name, price, description, image_url, seller_id, category_id
FROM Products  
WHERE available = :available  
ORDER BY RANDOM()  
LIMIT 5
''',
                             available=available)
        return [Product(*row) for row in rows]
    
    @staticmethod
    def get_filtered_top5(review, min_price, max_price, available=True):
        rows = app.db.execute('''
SELECT product_id AS id, name, price, description, image_url, seller_id, category_id
FROM Products  
WHERE available = :available  
AND price BETWEEN :min_price AND :max_price  
AND avg_review >= :review  
ORDER BY avg_review ASC, RANDOM()  
LIMIT 5;
''',
                             available=available, review=review, 
                             min_price=min_price, max_price=max_price
                             )
        return [Product(*row) for row in rows]