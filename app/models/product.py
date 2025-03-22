from flask import current_app as app


class Product:
    def __init__(self, id, name, description, price, available):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.available = available

    @staticmethod
    def get(id):
        rows = app.db.execute('''
SELECT id, name, description, price, available
FROM Products
WHERE id = :id
''',
                              id=id)
        return Product(*(rows[0])) if rows is not None else None

    @staticmethod
    def get_all(available=True):
        rows = app.db.execute('''
SELECT id, name, description, price, available
FROM Products
WHERE available = :available
''',
                            available=available)
        return [Product(*row) for row in rows]

    @staticmethod
    def get_all_top5(available=True):
        rows = app.db.execute('''
SELECT id, name, description, price, available
FROM Products
WHERE available = :available
LIMIT 5
''',
                             available=available)
        return [Product(*row) for row in rows]