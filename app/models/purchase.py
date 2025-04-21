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
    
    @staticmethod
    def get_orders_summary_by_user(uid):
        rows = app.db.execute('''
            SELECT 
                o.order_id,
                o.total_amount,
                COUNT(oi.order_item_id) AS item_count,
                o.fulfillment_status,
                o.created_at
            FROM Orders o
            JOIN Order_Items oi ON o.order_id = oi.order_id
            WHERE o.buyer_id = :uid
            GROUP BY o.order_id, o.total_amount, o.fulfillment_status, o.created_at
            ORDER BY o.created_at DESC
        ''', uid=uid)

        return [
            {
                "order_id": row[0],
                "total_amount": row[1],
                "item_count": row[2],
                "fulfillment_status": row[3],
                "created_at": row[4]
            }
            for row in rows
        ]

    @staticmethod
    def get_seller_orders(seller_id):
        """Fetch all orders where the user is the seller."""
        rows = app.db.execute('''
            SELECT 
                o.order_id,
                o.total_amount,
                COUNT(oi.order_item_id) AS item_count,
                o.fulfillment_status,
                o.created_at,
                u.firstname || ' ' || u.lastname AS buyer_name
            FROM Orders o
            JOIN Order_Items oi ON o.order_id = oi.order_id
            JOIN Users u ON o.buyer_id = u.id
            WHERE oi.seller_id = :seller_id
            GROUP BY o.order_id, o.total_amount, o.fulfillment_status, o.created_at, u.firstname, u.lastname
            ORDER BY o.created_at DESC
        ''', seller_id=seller_id)

        return [
            {
                "order_id": row[0],
                "total_amount": row[1],
                "item_count": row[2],
                "fulfillment_status": row[3],
                "created_at": row[4],
                "buyer_name": row[5]
            }
            for row in rows
        ]
