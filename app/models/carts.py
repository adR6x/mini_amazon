from flask import current_app as app
from sqlalchemy import text


class Cart:
    def __init__(self, cart_id, user_id, created_at, updated_at):
        self.cart_id = cart_id
        self.user_id = user_id
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def get_cart_by_user(user_id):
        rows = app.db.execute('''
            SELECT cart_id, user_id, created_at, updated_at
            FROM Carts
            WHERE user_id = :user_id
        ''', user_id=user_id)
        return Cart(*rows[0]) if rows else None

    @staticmethod
    def create_cart(user_id):
        print('userrr', user_id)
        rows = app.db.execute('''
            INSERT INTO Carts (user_id)
            VALUES (:user_id)
            ON CONFLICT (user_id) DO NOTHING
            RETURNING cart_id, user_id, created_at, updated_at
        ''', user_id=user_id)
        return Cart(*rows[0]) if rows else None

    @staticmethod
    def add_item_to_cart(user_id, product_id, quantity, unit_price, seller_id=None):
        try:
            # Get the cart_id
            cart = Cart.get_cart_by_user(user_id)
            if not cart:
                cart = Cart.create_cart(user_id)
                if not cart:
                    return None

            # If seller_id is provided, include it in the query
            if seller_id:
                rows = app.db.execute('''
                    INSERT INTO Cart_Items (cart_id, product_id, seller_id, quantity, unit_price)
                    VALUES (:cart_id, :product_id, :seller_id, :quantity, :unit_price)
                    ON CONFLICT (cart_id, product_id) DO UPDATE
                    SET quantity = Cart_Items.quantity + :quantity,
                        unit_price = :unit_price
                    RETURNING cart_item_id
                ''', cart_id=cart.cart_id, product_id=product_id, seller_id=seller_id,
                                      quantity=quantity, unit_price=unit_price)
            else:
                # If seller_id is not provided, omit it from the query
                rows = app.db.execute('''
                    INSERT INTO Cart_Items (cart_id, product_id, quantity, unit_price)
                    VALUES (:cart_id, :product_id, :quantity, :unit_price)
                    ON CONFLICT (cart_id, product_id) DO UPDATE
                    SET quantity = Cart_Items.quantity + :quantity,
                        unit_price = :unit_price
                    RETURNING cart_item_id
                ''', cart_id=cart.cart_id, product_id=product_id,
                                      quantity=quantity, unit_price=unit_price)

            return rows[0][0] if rows else None
        except Exception as e:
            import traceback
            print(f"Error in add_item_to_cart: {str(e)}")
            print(traceback.format_exc())
            return None

    @staticmethod
    def get_cart_items(user_id):
        try:
            print(f"Getting cart items for user: {user_id}")
            query = '''
                SELECT ci.cart_item_id, ci.product_id, p.name AS product_name, 
                       ci.quantity, ci.unit_price, ci.added_at
                FROM Cart_Items ci
                JOIN Carts c ON ci.cart_id = c.cart_id
                JOIN Products p ON ci.product_id = p.product_id
                WHERE c.user_id = :user_id
            '''
            print(f"Executing get_cart_items query: {query}")
            rows = app.db.execute(query, user_id=user_id)
            print(f"Found {len(rows) if rows else 0} items")
            return rows
        except Exception as e:
            import traceback
            print(f"Error getting cart items: {str(e)}")
            print(traceback.format_exc())
            return []

    @staticmethod
    def update_item_quantity(cart_item_id, quantity):
        try:
            app.db.execute('''
                UPDATE Cart_Items
                SET quantity = :quantity
                WHERE cart_item_id = :cart_item_id
            ''', cart_item_id=cart_item_id, quantity=quantity)
            return True
        except Exception as e:
            import traceback
            print(f"Error updating quantity: {str(e)}")
            print(traceback.format_exc())
            return False

    @staticmethod
    def remove_item_from_cart(cart_item_id):
        try:
            app.db.execute('''
                DELETE FROM Cart_Items
                WHERE cart_item_id = :cart_item_id
            ''', cart_item_id=cart_item_id)
            return True
        except Exception as e:
            import traceback
            print(f"Error removing item: {str(e)}")
            print(traceback.format_exc())
            return False

    @staticmethod
    def checkout(user_id):
        try:
            print(f"Starting Cart.checkout for user_id: {user_id}")
            
            # First, check if the user has a cart
            cart = app.db.execute('''
                SELECT cart_id 
                FROM Carts 
                WHERE user_id = :user_id
            ''', user_id=user_id)
            print(f"Found cart: {cart}")
            
            if not cart:
                print("No cart found for user")
                return {'success': False, 'message': 'No cart found. Please add items to your cart first.'}
            
            with app.db.engine.begin() as conn:
                # Get cart items with product and inventory info
                print("Fetching cart items with inventory info...")
                cart_items = conn.execute(text('''
                    SELECT 
                        ci.cart_item_id,
                        ci.product_id,
                        p.name AS product_name,
                        ci.quantity,
                        ci.unit_price,
                        i.seller_id,
                        i.quantity_available
                    FROM Cart_Items ci
                    JOIN Carts c ON ci.cart_id = c.cart_id
                    JOIN Products p ON ci.product_id = p.product_id
                    JOIN Inventory i ON ci.product_id = i.product_id
                    WHERE c.user_id = :user_id
                '''), {'user_id': user_id}).fetchall()
                print(f"Found {len(cart_items) if cart_items else 0} items with inventory")

                if not cart_items:
                    print("Cart is empty or no inventory found")
                    return {'success': False, 'message': 'Your cart is empty or the items are no longer available.'}

                # Get buyer's balance
                buyer = conn.execute(text('''
                    SELECT balance
                    FROM Users
                    WHERE id = :user_id
                '''), {'user_id': user_id}).fetchone()
                
                if not buyer:
                    print("Buyer not found")
                    return {'success': False, 'message': 'User account not found. Please try logging in again.'}
                
                if buyer.balance is None:
                    print("Buyer balance is None")
                    return {'success': False, 'message': 'Your account balance is not set. Please topup your balance first.'}
                
                print(f"Buyer balance: ${buyer.balance}")

                # Calculate total amount
                total_amount = sum(item.quantity * item.unit_price for item in cart_items)
                print(f"Total amount: ${total_amount}")

                # Check buyer's balance
                if buyer.balance < total_amount:
                    print(f"Insufficient balance: ${buyer.balance} < ${total_amount}")
                    return {'success': False, 'message': f'Insufficient balance. You need ${total_amount - buyer.balance:.2f} more to complete this purchase.'}

                # Check inventory for all items
                for item in cart_items:
                    if item.quantity_available < item.quantity:
                        print(f"Insufficient inventory for {item.product_name}: requested {item.quantity}, available {item.quantity_available}")
                        return {'success': False, 'message': f'Insufficient inventory for {item.product_name}. Only {item.quantity_available} available.'}

                # Create order with initial status 'pending'
                print("Creating order...")
                order_id = conn.execute(text('''
                    INSERT INTO Orders (order_id, buyer_id, total_amount, fulfillment_status)
                    VALUES (DEFAULT, :buyer_id, :total_amount, 'pending')
                    RETURNING order_id
                '''), {
                    'buyer_id': user_id,
                    'total_amount': total_amount
                }).fetchone()[0]
                print(f"Created order {order_id}")

                # Create order items and update inventory
                for item in cart_items:
                    # Create order item with initial status 'pending'
                    conn.execute(text('''
                        INSERT INTO Order_Items (order_item_id, order_id, product_id, seller_id, quantity, unit_price, fulfillment_status)
                        VALUES (DEFAULT, :order_id, :product_id, :seller_id, :quantity, :unit_price, 'pending')
                    '''), {
                        'order_id': order_id,
                        'product_id': item.product_id,
                        'seller_id': item.seller_id,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price
                    })

                    # Update inventory
                    conn.execute(text('''
                        UPDATE Inventory
                        SET quantity_available = quantity_available - :quantity
                        WHERE product_id = :product_id AND seller_id = :seller_id
                    '''), {
                        'quantity': item.quantity,
                        'product_id': item.product_id,
                        'seller_id': item.seller_id
                    })

                    # Update seller's balance
                    seller_amount = item.quantity * item.unit_price
                    conn.execute(text('''
                        UPDATE Users
                        SET balance = balance + :amount
                        WHERE id = :seller_id
                    '''), {
                        'amount': seller_amount,
                        'seller_id': item.seller_id
                    })

                # Update buyer's balance
                conn.execute(text('''
                    UPDATE Users
                    SET balance = balance - :amount
                    WHERE id = :user_id
                '''), {
                    'amount': total_amount,
                    'user_id': user_id
                })

                # Clear cart
                conn.execute(text('''
                    DELETE FROM Cart_Items
                    WHERE cart_id IN (SELECT cart_id FROM Carts WHERE user_id = :user_id)
                '''), {'user_id': user_id})

                print("Checkout completed successfully")
                return {'success': True, 'message': 'Order placed successfully!', 'order_id': order_id}

        except Exception as e:
            import traceback
            print(f"Error in Cart.checkout: {str(e)}")
            print(traceback.format_exc())
            return {'success': False, 'message': f'An error occurred during checkout: {str(e)}'}

    @staticmethod
    def fulfill_order_item(order_item_id, seller_id):
        """Fulfill a single order item and update order status if all items are fulfilled."""
        try:
            with app.db.engine.begin() as conn:
                # First verify the seller owns this order item
                order_item = conn.execute(text('''
                    SELECT oi.order_id, oi.fulfillment_status
                    FROM Order_Items oi
                    WHERE oi.order_item_id = :order_item_id AND oi.seller_id = :seller_id
                '''), {
                    'order_item_id': order_item_id,
                    'seller_id': seller_id
                }).fetchone()

                if not order_item:
                    return {'success': False, 'message': 'Order item not found or unauthorized.'}

                if order_item.fulfillment_status == 'fulfilled':
                    return {'success': False, 'message': 'Order item already fulfilled.'}

                # Update the order item status
                conn.execute(text('''
                    UPDATE Order_Items
                    SET fulfillment_status = 'fulfilled',
                        fulfilled_at = CURRENT_TIMESTAMP
                    WHERE order_item_id = :order_item_id
                '''), {'order_item_id': order_item_id})

                # Check if all items in the order are fulfilled
                pending_items = conn.execute(text('''
                    SELECT COUNT(*) as pending_count
                    FROM Order_Items
                    WHERE order_id = :order_id AND fulfillment_status = 'pending'
                '''), {'order_id': order_item.order_id}).fetchone()

                if pending_items.pending_count == 0:
                    # All items are fulfilled, update order status
                    conn.execute(text('''
                        UPDATE Orders
                        SET fulfillment_status = 'fulfilled'
                        WHERE order_id = :order_id
                    '''), {'order_id': order_item.order_id})

                return {'success': True, 'message': 'Order item fulfilled successfully.'}

        except Exception as e:
            print(f"Error in fulfill_order_item: {str(e)}")
            return {'success': False, 'message': f'Error fulfilling order item: {str(e)}'}

    @staticmethod
    def get_order_status(order_id, user_id):
        """Get the status of an order and its items."""
        try:
            with app.db.engine.begin() as conn:
                # Verify the user has access to this order
                order = conn.execute(text('''
                    SELECT o.order_id, o.fulfillment_status, o.total_amount
                    FROM Orders o
                    WHERE o.order_id = :order_id AND o.buyer_id = :user_id
                '''), {
                    'order_id': order_id,
                    'user_id': user_id
                }).fetchone()

                if not order:
                    return {'success': False, 'message': 'Order not found or unauthorized.'}

                # Get all items in the order
                items = conn.execute(text('''
                    SELECT 
                        oi.order_item_id,
                        oi.product_id,
                        p.name AS product_name,
                        oi.quantity,
                        oi.unit_price,
                        oi.fulfillment_status,
                        oi.fulfilled_at
                    FROM Order_Items oi
                    JOIN Products p ON oi.product_id = p.product_id
                    WHERE oi.order_id = :order_id
                '''), {'order_id': order_id}).fetchall()

                return {
                    'success': True,
                    'order': {
                        'order_id': order.order_id,
                        'status': order.fulfillment_status,
                        'total_amount': order.total_amount,
                        'items': [{
                            'order_item_id': item.order_item_id,
                            'product_name': item.product_name,
                            'quantity': item.quantity,
                            'unit_price': item.unit_price,
                            'status': item.fulfillment_status,
                            'fulfilled_at': item.fulfilled_at
                        } for item in items]
                    }
                }

        except Exception as e:
            print(f"Error in get_order_status: {str(e)}")
            return {'success': False, 'message': f'Error getting order status: {str(e)}'}
