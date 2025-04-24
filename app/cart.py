from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import current_user, login_required
from app.models.carts import Cart
import app.db
from datetime import datetime
from flask import current_app as app
import traceback

cart = Blueprint('cart', __name__)


@cart.route('/cart')
@login_required
def cart_page():
    try:
        # Fetch cart items for the logged-in user
        cart_items = Cart.get_cart_items(current_user.id)

        # Calculate total amount - cart_items contains Row objects, not custom objects
        total_amount = sum(item[3] * item[4]
                           for item in cart_items) if cart_items else 0
        # Indexes: 3 = quantity, 4 = unit_price

        # Add total_price to each cart item
        enhanced_cart_items = []
        for item in cart_items:
            # Convert the Row to a dict and add the total_price
            item_dict = {
                'cart_item_id': item[0],
                'product_id': item[1],
                'product_name': item[2],
                'quantity': item[3],
                'unit_price': item[4],
                'added_at': item[5],
                'total_price': item[3] * item[4]  # quantity * unit_price
            }
            enhanced_cart_items.append(item_dict)

        # Get user's address
        user_address = Cart.get_user_address(current_user.id)

        # Get applied coupons
        applied_coupons = []
        total_discount = 0
        
        if 'applied_coupons' in session:
            for coupon_id in session['applied_coupons']:
                coupon = app.db.execute("""
                    SELECT c.*, u.username as seller_name
                    FROM coupons c
                    JOIN users u ON c.seller_id = u.id
                    WHERE c.id = %s AND c.is_active = true AND c.expiration_date > NOW()
                """, (coupon_id,)).fetchone()
                
                if coupon:
                    # Calculate discount for this seller's products
                    seller_items = [item for item in cart_items if item[6] == coupon.seller_id]
                    seller_subtotal = sum(item[3] * item[4] for item in seller_items)
                    discount_amount = min(seller_subtotal * (coupon.discount_percent / 100), coupon.max_discount)
                    
                    applied_coupons.append({
                        'id': coupon.id,
                        'code': coupon.code,
                        'discount_amount': discount_amount,
                        'seller_name': coupon.seller_name
                    })
                    total_discount += discount_amount
        
        total = total_amount - total_discount

        return render_template('cart.html',
                               cart_items=enhanced_cart_items,
                               total_amount=round(total_amount, 2),
                               user_address=user_address,
                               total_discount=round(total_discount, 2),
                               total=round(total, 2),
                               applied_coupons=applied_coupons)
    except Exception as e:
        import traceback
        print(f"Error in cart_page: {str(e)}")
        print(traceback.format_exc())
        return render_template('cart.html', cart_items=[], total_amount=0, error=str(e))


@cart.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    try:
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity', '1')
        unit_price = request.form.get('unit_price')

        print(
            f"Request data: product_id={product_id}, quantity={quantity}, unit_price={unit_price}")

        # Validate input
        if not product_id or not unit_price:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        try:
            product_id = int(product_id)
            quantity = int(quantity)
            unit_price = float(unit_price)

            if quantity <= 0:
                return jsonify({'success': False, 'message': 'Quantity must be positive'}), 400
        except ValueError as e:
            print(f"Value conversion error: {str(e)}")
            return jsonify({'success': False, 'message': 'Invalid input values'}), 400

        # Debug user info
        print(f"Current user ID: {current_user.id}")

        # Check if cart exists or create one
        cart = Cart.get_cart_by_user(current_user.id)
        print(f"Existing cart: {cart}")

        if not cart:
            print("Creating new cart")
            cart = Cart.create_cart(current_user.id)
            print(f"New cart: {cart}")

            if not cart:
                return jsonify({'success': False, 'message': 'Failed to create cart'}), 500

        # Add item to cart
        print(f"Adding item: {product_id}, {quantity}, {unit_price}")
        cart_item_id = Cart.add_item_to_cart(
            current_user.id, product_id, quantity, unit_price)
        print(f"Result cart_item_id: {cart_item_id}")

        if cart_item_id:
            return jsonify({'success': True, 'message': 'Item added to cart successfully!'}), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to add item to cart'}), 500

    except Exception as e:
        import traceback
        print(f"Error adding to cart: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500


@cart.route('/update_quantity', methods=['POST'])
@login_required
def update_quantity():
    try:
        cart_item_id = request.form.get('cart_item_id')
        quantity = request.form.get('quantity')

        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not cart_item_id or not quantity:
            if is_ajax:
                return jsonify({'success': False, 'message': 'Invalid request'}), 400
            else:
                flash('Invalid request. Please try again.', 'danger')
                return redirect(url_for('cart.cart_page'))

        # Convert to int (validate input)
        try:
            cart_item_id = int(cart_item_id)
            quantity = int(quantity)
            if quantity <= 0:
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Quantity must be greater than zero'}), 400
                else:
                    flash('Quantity must be greater than zero.', 'danger')
                    return redirect(url_for('cart.cart_page'))
        except ValueError:
            if is_ajax:
                return jsonify({'success': False, 'message': 'Invalid input'}), 400
            else:
                flash('Invalid input. Please try again.', 'danger')
                return redirect(url_for('cart.cart_page'))

        # Update the quantity
        success = Cart.update_item_quantity(cart_item_id, quantity)

        if is_ajax:
            if success:
                return jsonify({'success': True, 'message': 'Cart updated successfully!'}), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to update cart'}), 500
        else:
            if success:
                flash('Cart updated successfully!', 'success')
            else:
                flash('Failed to update cart.', 'danger')

            return redirect(url_for('cart.cart_page'))
    except Exception as e:
        import traceback
        print(f"Error in update_quantity: {str(e)}")
        print(traceback.format_exc())

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'An error occurred'}), 500
        else:
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('cart.cart_page'))


@cart.route('/remove_item', methods=['POST'])
@login_required
def remove_item():
    try:
        cart_item_id = request.form.get('cart_item_id')

        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not cart_item_id:
            if is_ajax:
                return jsonify({'success': False, 'message': 'Invalid request'}), 400
            else:
                flash('Invalid request. Please try again.', 'danger')
                return redirect(url_for('cart.cart_page'))

        # Convert to int (validate input)
        try:
            cart_item_id = int(cart_item_id)
        except ValueError:
            if is_ajax:
                return jsonify({'success': False, 'message': 'Invalid input'}), 400
            else:
                flash('Invalid input. Please try again.', 'danger')
                return redirect(url_for('cart.cart_page'))

        # Remove the item
        success = Cart.remove_item_from_cart(cart_item_id)

        if is_ajax:
            if success:
                return jsonify({'success': True, 'message': 'Item removed from cart!'}), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to remove item.'}), 500
        else:
            if success:
                flash('Item removed from cart!', 'success')
            else:
                flash('Failed to remove item.', 'danger')

            return redirect(url_for('cart.cart_page'))
    except Exception as e:
        import traceback
        print(f"Error in remove_item: {str(e)}")
        print(traceback.format_exc())

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'An error occurred'}), 500
        else:
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('cart.cart_page'))


@cart.route('/checkout', methods=['POST'])
@login_required
def checkout():
    try:
        print("Starting checkout process for user:", current_user.id)
        result = Cart.checkout(current_user.id)
        print("Checkout result:", result)
        
        if result['success']:
            print("Checkout successful, redirecting to purchases page")
            flash('Order placed successfully!', 'success')
            return redirect(url_for('users.purchases'))
        else:
            print("Checkout failed:", result['message'])
            flash(result['message'], 'danger')
            return redirect(url_for('cart.cart_page'))
    except Exception as e:
        import traceback
        print(f"Error in checkout route: {str(e)}")
        print(traceback.format_exc())
        flash('An error occurred during checkout. Please try again.', 'danger')
        return redirect(url_for('cart.cart_page'))


@cart.route('/apply_coupon', methods=['POST'])
@login_required
def apply_coupon():
    try:
        # Get cart items to check if user has items from the coupon's seller
        cart_items = Cart.get_cart_items(current_user.id)
        if not cart_items:
            flash('Your cart is empty. Add items before applying coupons.', 'warning')
            return redirect(url_for('cart.cart_page'))

        coupon_code = request.form.get('coupon_code')
        if not coupon_code:
            flash('Please enter a coupon code', 'warning')
            return redirect(url_for('cart.cart_page'))

        # Get coupon details
        coupon_result = app.db.execute("""
            SELECT c.id, c.code, c.seller_id, c.discount_amount, c.expiration_date, c.is_active,
                   CONCAT(u.firstname, ' ', u.lastname) as seller_name
            FROM Coupons c
            JOIN Users u ON c.seller_id = u.id
            WHERE c.code = :code 
            AND c.is_active = true
            AND c.expiration_date > CURRENT_TIMESTAMP
        """, code=coupon_code)

        if not coupon_result:
            flash('Invalid or expired coupon code', 'error')
            return redirect(url_for('cart.cart_page'))

        coupon = coupon_result[0]  # Get the first row

        # Check if coupon is already applied
        applied_coupons = session.get('applied_coupons', [])
        if any(c['id'] == coupon[0] for c in applied_coupons):  # coupon[0] is the id
            flash('This coupon is already applied', 'warning')
            return redirect(url_for('cart.cart_page'))

        # Get cart items with seller information
        cart_items_with_seller = app.db.execute("""
            SELECT ci.cart_item_id, ci.product_id, p.name AS product_name, 
                   ci.quantity, ci.unit_price, ci.added_at, p.seller_id
            FROM Cart_Items ci
            JOIN Carts c ON ci.cart_id = c.cart_id
            JOIN Products p ON ci.product_id = p.product_id
            WHERE c.user_id = :user_id
        """, user_id=current_user.id)

        # Check if user has items from this seller
        seller_items = [item for item in cart_items_with_seller if item[6] == coupon[2]]  # coupon[2] is the seller_id
        if not seller_items:
            flash(f'You need items from {coupon[6]} to use this coupon. Add their products to your cart first.', 'warning')
            return redirect(url_for('cart.cart_page'))

        # Add coupon to session
        applied_coupons.append({
            'id': coupon[0],  # id
            'code': coupon[1],  # code
            'discount_amount': coupon[3],  # discount_amount
            'seller_id': coupon[2],  # seller_id
            'seller_name': coupon[6]  # seller_name
        })
        session['applied_coupons'] = applied_coupons

        flash('Coupon applied successfully!', 'success')
        return redirect(url_for('cart.cart_page'))

    except Exception as e:
        print(f"Error applying coupon: {str(e)}")
        print(traceback.format_exc())
        flash('An error occurred while applying the coupon', 'error')
        return redirect(url_for('cart.cart_page'))


@cart.route('/cart/remove_coupon/<int:coupon_id>', methods=['POST'])
@login_required
def remove_coupon(coupon_id):
    if 'applied_coupons' in session and coupon_id in session['applied_coupons']:
        session['applied_coupons'].remove(coupon_id)
        session.modified = True
        flash('Coupon removed', 'info')
    return redirect(url_for('cart.cart_page'))
