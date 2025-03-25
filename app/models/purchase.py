from flask import current_app as app


class Purchase:
    def __init__(self, id, uid, pid, time_purchased):
        self.id = id
        self.uid = uid
        self.pid = pid
        self.time_purchased = time_purchased

    @staticmethod
    def get(id):
        rows = app.db.execute('''
SELECT id, uid, pid, time_purchased
FROM Purchases
WHERE id = :id
''',
                              id=id)
        return Purchase(*(rows[0])) if rows else None

    @staticmethod
    def get_all_by_uid_since(uid, since):
        rows = app.db.execute('''
SELECT pu.id AS purchase_id, p.name AS product_name, p.price, pu.time_purchased
FROM Purchases pu
JOIN Products p on pu.pid=p.id
WHERE pu.uid = :uid
AND time_purchased >= :since
ORDER BY time_purchased DESC
''',
                              uid=uid,
                              since=since)
        return [{
            "purchase_id": row[0],
            "product_name": row[1],
            "price": row[2],
            "time_purchased": row[3]
        }
        for row in rows]

    @staticmethod
    def get_all_purchases_by_user(uid):
        """Fetch all purchases for a given user, including product details."""
        rows = app.db.execute('''
        SELECT pu.id, p.name AS product_name, p.price, pu.time_purchased
        FROM Purchases pu
        JOIN Products p ON pu.pid = p.id
        WHERE pu.uid = :uid
        ORDER BY pu.time_purchased DESC
        ''', uid=uid)

        return [
            {
                "purchase_id": row[0],
                "product_name": row[1],
                "price": row[2],
                "time_purchased": row[3]
            }
            for row in rows
        ]


