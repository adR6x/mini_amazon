from flask import current_app as app


class Product:
    def __init__(self, id, name, description, price, available, avg_review):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.available = available
        self.avg_review = avg_review

    @staticmethod
    def get(id):
        rows = app.db.execute('''
SELECT id, name, description, price, available, avg_review
FROM Products
WHERE id = :id
''',
                              id=id)
        return Product(*(rows[0])) if rows is not None else None

    @staticmethod
    def get_all(available=True):
        rows = app.db.execute('''
SELECT id, name, description, price, available, avg_review
FROM Products
WHERE available = :available
''',
                            available=available)
        return [Product(*row) for row in rows]

    @staticmethod
    def get_all_top5(available=True):
        rows = app.db.execute('''
SELECT id, name, description, price, available, avg_review  
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
SELECT id, name, description, price, available, avg_review  
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