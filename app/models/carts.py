from flask import current_app as app


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
            rows = app.db.execute('''
                SELECT ci.cart_item_id, ci.product_id, p.name AS product_name, 
                       ci.quantity, ci.unit_price, ci.added_at
                FROM Cart_Items ci
                JOIN Carts c ON ci.cart_id = c.cart_id
                JOIN Products p ON ci.product_id = p.product_id
                WHERE c.user_id = :user_id
            ''', user_id=user_id)
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
