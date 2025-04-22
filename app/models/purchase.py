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
    def get_orders_summary_by_user(uid, page=1, per_page=10):
        """Fetch all orders where the user is the buyer with pagination."""
        offset = (page - 1) * per_page
        
        # Get total count
        count_rows = app.db.execute('''
            SELECT COUNT(DISTINCT o.order_id)
            FROM Orders o
            WHERE o.buyer_id = :uid
        ''', uid=uid)
        total_count = count_rows[0][0] if count_rows else 0
        
        # Get paginated results
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
            LIMIT :limit OFFSET :offset
        ''', uid=uid, limit=per_page, offset=offset)

        orders = [
            {
                "order_id": row[0],
                "total_amount": row[1],
                "item_count": row[2],
                "fulfillment_status": row[3],
                "created_at": row[4]
            }
            for row in rows
        ]
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return {
            'orders': orders,
            'total_pages': total_pages,
            'current_page': page,
            'per_page': per_page,
            'total_count': total_count
        }

    @staticmethod
    def get_seller_orders(seller_id, page=1, per_page=10):
        """Fetch all orders where the user is the seller with pagination."""
        offset = (page - 1) * per_page
        
        # Get total count
        count_rows = app.db.execute('''
            SELECT COUNT(DISTINCT o.order_id)
            FROM Orders o
            JOIN Order_Items oi ON o.order_id = oi.order_id
            WHERE oi.seller_id = :seller_id
        ''', seller_id=seller_id)
        total_count = count_rows[0][0] if count_rows else 0
        
        # Get paginated results
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
            LIMIT :per_page OFFSET :offset
        ''', seller_id=seller_id, per_page=per_page, offset=offset)

        orders = [
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
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return {
            'orders': orders,
            'total_pages': total_pages,
            'current_page': page,
            'per_page': per_page,
            'total_count': total_count
        }

    @staticmethod
    def get_purchase_details(order_id, user_id):
        """Fetch detailed information about a specific purchase."""
        rows = app.db.execute('''
            SELECT 
                oi.order_item_id,
                p.name AS product_name,
                oi.quantity,
                oi.unit_price,
                oi.fulfillment_status,
                u.firstname || ' ' || u.lastname AS seller_name
            FROM Order_Items oi
            JOIN Products p ON oi.product_id = p.product_id
            JOIN Users u ON oi.seller_id = u.id
            JOIN Orders o ON oi.order_id = o.order_id
            WHERE o.order_id = :order_id AND o.buyer_id = :user_id
        ''', order_id=order_id, user_id=user_id)

        return [
            {
                "order_item_id": row[0],
                "product_name": row[1],
                "quantity": row[2],
                "unit_price": row[3],
                "fulfillment_status": row[4],
                "seller_name": row[5]
            }
            for row in rows
        ]

    @staticmethod
    def get_order_details(order_id, seller_id):
        """Fetch detailed information about a specific order for seller's products."""
        rows = app.db.execute('''
            SELECT 
                oi.order_item_id,
                p.name AS product_name,
                oi.quantity,
                oi.unit_price,
                oi.fulfillment_status,
                u.firstname || ' ' || u.lastname AS buyer_name,
                u.address AS buyer_address,
                oi.order_id
            FROM Order_Items oi
            JOIN Products p ON oi.product_id = p.product_id
            JOIN Orders o ON oi.order_id = o.order_id
            JOIN Users u ON o.buyer_id = u.id
            WHERE oi.order_id = :order_id 
            AND oi.seller_id = :seller_id
            ORDER BY oi.order_item_id
        ''', order_id=order_id, seller_id=seller_id)

        return [
            {
                "order_item_id": row[0],
                "product_name": row[1],
                "quantity": row[2],
                "unit_price": row[3],
                "fulfillment_status": row[4],
                "buyer_name": row[5],
                "buyer_address": row[6],
                "order_id": row[7]
            }
            for row in rows
        ]
