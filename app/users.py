from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask_login import login_required
from .models.purchase import Purchase 
from .models.carts import Cart
from flask import current_app as app
from werkzeug.security import generate_password_hash
import re
from datetime import datetime

from .models.user import User
from .models.product import Product
from .models.seller_review import SellerReview

from flask import Blueprint
bp = Blueprint('users', __name__)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_auth(form.email.data, form.password.data)
        if user is None:
            flash('Invalid email or password')
            return redirect(url_for('users.login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index.index')

        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(),
                                       EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        if User.email_exists(email.data):
            raise ValidationError('Already a user with this email.')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.register(form.email.data,
                         form.password.data,
                         form.firstname.data,
                         form.lastname.data):
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index.index'))


@bp.route('/purchases')
@login_required
def purchases():
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Validate and constrain per_page to allowed values
    allowed_per_page = [10, 15]
    if per_page not in allowed_per_page:
        per_page = 10
    
    # Fetch paginated purchases for the logged-in user
    result = Purchase.get_orders_summary_by_user(current_user.id, page, per_page)
    
    return render_template('purchases.html',
                         orders=result['orders'],
                         current_page=result['current_page'],
                         total_pages=result['total_pages'],
                         per_page=result['per_page'],
                         total_count=result['total_count'],
                         allowed_per_page=allowed_per_page)


@bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        try:
            # Retrieve form data
            new_firstname = request.form.get('firstname')
            new_lastname = request.form.get('lastname')
            new_email = request.form.get('email')
            new_password = request.form.get('password')
            new_address = request.form.get('address')
            new_balance = request.form.get('balance')
            new_balance = float(new_balance) if new_balance else 0.00

            # Validation: prevent negative balance
            if new_balance < 0:
                flash("Balance cannot be negative.", "danger")
                return redirect(url_for('users.account'))
            
            # Update the user details in the database
            if new_password:
                hashed_password = generate_password_hash(new_password)
                app.db.execute('''
                    UPDATE Users
                    SET firstname = :firstname,
                        lastname = :lastname,
                        email = :email,
                        password = :password,
                        address = :address,
                        balance = :balance
                    WHERE id = :id
                ''', id=current_user.id, firstname=new_firstname, lastname=new_lastname, email=new_email, password=hashed_password, address=new_address, balance=new_balance)
            else:
                app.db.execute('''
                    UPDATE Users
                    SET firstname = :firstname,
                        lastname = :lastname,
                        email = :email,
                        address = :address,
                        balance = :balance
                    WHERE id = :id
                ''', id=current_user.id, firstname=new_firstname, lastname=new_lastname, email=new_email, address=new_address, balance=new_balance)

            flash("Profile updated successfully!", "success")
        except Exception as e:
            flash("Error updating profile: " + str(e), "danger")

    # Fetch the current user details
    try:
        user_row = app.db.execute('''
            SELECT id, email, firstname, lastname, address, balance
            FROM Users
            WHERE id = :id
        ''', id=current_user.id)[0]
        
        # Convert Row to dictionary and handle None balance
        user_details = {
            'id': user_row.id,
            'email': user_row.email,
            'firstname': user_row.firstname,
            'lastname': user_row.lastname,
            'address': user_row.address,
            'balance': user_row.balance if user_row.balance is not None else 0.00
        }

        # Debug: Check inventory
        inventory = app.db.execute('''
            SELECT i.product_id, p.name, i.quantity_available, i.price
            FROM Inventory i
            JOIN Products p ON i.product_id = p.product_id
            WHERE i.seller_id = :id
        ''', id=current_user.id)
        print(f"Debug: Inventory found: {inventory}")

        # Check if user is a seller (has items in inventory)
        is_seller = len(inventory) > 0
        print(f"Debug: Is seller: {is_seller}")
        print(f"Debug: User ID: {current_user.id}")

        # Add is_seller to user_details
        user_details['is_seller'] = is_seller

        # Get seller stats if user is a seller
        seller_stats = None
        if is_seller:
            print("Debug: Fetching seller stats")
            
            # Get seller stats
            total_products = len(inventory)
            print(f"Debug: Total products: {total_products}")

            total_sales = app.db.execute('''
                SELECT COUNT(*) FROM Orders o
                JOIN Order_Items oi ON o.order_id = oi.order_id
                JOIN Products p ON oi.product_id = p.product_id
                WHERE p.seller_id = :id
            ''', id=current_user.id)[0][0]
            print(f"Debug: Total sales: {total_sales}")

            avg_rating = app.db.execute('''
                SELECT COALESCE(AVG(rating), 0) FROM Seller_Reviews WHERE seller_id = :id
            ''', id=current_user.id)[0][0]
            print(f"Debug: Average rating: {avg_rating}")

            # Get coupon statistics
            coupon_stats = app.db.execute('''
                SELECT 
                    COUNT(*) as total_coupons,
                    SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_coupons,
                    SUM(CASE WHEN NOT is_active THEN 1 ELSE 0 END) as inactive_coupons
                FROM Coupons
                WHERE seller_id = :id
            ''', id=current_user.id)[0]

            seller_stats = {
                'total_products': total_products,
                'total_sales': total_sales,
                'average_rating': avg_rating,
                'total_coupons': coupon_stats[0],
                'active_coupons': coupon_stats[1],
                'inactive_coupons': coupon_stats[2]
            }
            print(f"Debug: Seller stats: {seller_stats}")

        print(f"Debug: Final user details: {user_details}")
        return render_template('profile.html', user=user_details, seller_stats=seller_stats)
    except Exception as e:
        print(f"Debug: Error in account route: {str(e)}")
        flash("Error loading profile: " + str(e), "danger")
        return redirect(url_for('index.index'))

@bp.route('/user/<int:user_id>')
def public_profile(user_id):
    user = app.db.execute('''
        SELECT id, firstname, lastname, email, address
        FROM Users
        WHERE id = :id
    ''', id=user_id)

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('index'))  # or a 404 page

    user = user[0]

    # Check if this user is a seller (has at least 1 product listed)
    is_seller_result = app.db.execute('''
        SELECT EXISTS (
            SELECT 1 FROM Products WHERE seller_id = :id
        ) AS is_seller
    ''', id=user_id)

    is_seller = bool(is_seller_result[0][0])


    # Get seller reviews if seller
    reviews = []
    if is_seller:
        reviews = app.db.execute('''
            SELECT sr.rating, sr.review_text, sr.created_at, u.firstname, u.lastname
            FROM seller_reviews sr
            JOIN Users u ON sr.reviewer_id = u.id
            WHERE sr.seller_id = :id
        ''', id=user_id)


    return render_template('public_profile.html', user=user, is_seller=is_seller, reviews=reviews)

@bp.route('/orders')
@login_required
def orders():
    """Route for viewing orders where the user is the seller."""
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Validate and constrain per_page to allowed values
    allowed_per_page = [10, 15]
    if per_page not in allowed_per_page:
        per_page = 10
    
    # Fetch paginated orders for the logged-in seller
    result = Purchase.get_seller_orders(current_user.id, page, per_page)
    
    return render_template('orders.html',
                         orders=result['orders'],
                         current_page=result['current_page'],
                         total_pages=result['total_pages'],
                         per_page=per_page,
                         total_count=result['total_count'],
                         allowed_per_page=allowed_per_page)

@bp.route('/purchases/<int:order_id>')
@login_required
def purchase_details(order_id):
    """View detailed information about a specific purchase."""
    details = Purchase.get_purchase_details(order_id, current_user.id)
    if not details:
        flash('Purchase not found or unauthorized.', 'danger')
        return redirect(url_for('users.purchases'))
    return render_template('purchase_details.html', details=details)

@bp.route('/orders/<int:order_id>')
@login_required
def order_details(order_id):
    """View detailed information about a specific order for seller's products."""
    # Force a fresh fetch of the order details
    details = Purchase.get_order_details(order_id, current_user.id)
    if not details:
        flash('Order not found or unauthorized.', 'danger')
        return redirect(url_for('users.orders'))
    return render_template('order_details.html', details=details)

@bp.route('/orders/<int:order_id>/fulfill', methods=['POST'])
@login_required
def fulfill_order(order_id):
    """Update the fulfillment status of an order item."""
    order_item_id = request.form.get('order_item_id')
    fulfillment_status = request.form.get('fulfillment_status')
    
    if not order_item_id or not fulfillment_status or fulfillment_status not in ['pending', 'fulfilled']:
        flash('Invalid request.', 'danger')
        return redirect(url_for('users.order_details', order_id=order_id))
    
    result = Cart.fulfill_order_item(order_item_id, current_user.id, fulfillment_status)
    if result['success']:
        flash(f'Order status updated to {fulfillment_status}.', 'success')
    else:
        flash(result['message'], 'danger')
    return redirect(url_for('users.order_details', order_id=order_id))

@bp.route('/profile/<int:user_id>')
def view_profile(user_id):
    """View a user's public profile."""
    try:
        print(f"Debug: Fetching profile for user_id: {user_id}")

        # Get user details
        user_result = app.db.execute('''
            SELECT id, email, firstname, lastname, address
            FROM Users
            WHERE id = :id
        ''', id=user_id)

        if not user_result:
            print("Debug: User not found")
            flash('User not found', 'error')
            return redirect(url_for('index.index'))

        user_row = user_result[0]
        print(f"Debug: User found: {user_row}")

        # Convert Row to dictionary
        user = {
            'id': user_row.id,
            'email': user_row.email,
            'firstname': user_row.firstname,
            'lastname': user_row.lastname,
            'address': user_row.address
        }
        print(f"Debug: User dictionary: {user}")

        # Debug: Check inventory
        inventory = app.db.execute('''
            SELECT i.product_id, p.name, i.quantity_available, i.price
            FROM Inventory i
            JOIN Products p ON i.product_id = p.product_id
            WHERE i.seller_id = :id
        ''', id=user_id)
        print(f"Debug: Inventory found: {inventory}")

        # Check if user is a seller (has items in inventory)
        is_seller = len(inventory) > 0
        print(f"Debug: Is seller: {is_seller}")

        # Add is_seller to user
        user['is_seller'] = is_seller

        # Get user's seller stats and reviews if they are a seller
        seller_stats = None
        reviews = None
        if is_seller:
            print("Debug: Fetching seller stats and reviews")
            
            # Get seller stats
            total_products = len(inventory)
            print(f"Debug: Total products: {total_products}")

            total_sales = app.db.execute('''
                SELECT COUNT(*) FROM Orders o
                JOIN Order_Items oi ON o.order_id = oi.order_id
                JOIN Products p ON oi.product_id = p.product_id
                WHERE p.seller_id = :id
            ''', id=user_id)[0][0]
            print(f"Debug: Total sales: {total_sales}")

            avg_rating = app.db.execute('''
                SELECT COALESCE(AVG(rating), 0) FROM Seller_Reviews WHERE seller_id = :id
            ''', id=user_id)[0][0]
            print(f"Debug: Average rating: {avg_rating}")

            seller_stats = {
                'total_products': total_products,
                'total_sales': total_sales,
                'average_rating': avg_rating
            }
            print(f"Debug: Seller stats: {seller_stats}")

            # Get seller reviews
            reviews_result = app.db.execute('''
                SELECT sr.rating, sr.review_text, sr.created_at, 
                       u.firstname as reviewer_firstname, u.lastname as reviewer_lastname
                FROM Seller_Reviews sr
                JOIN Users u ON sr.reviewer_id = u.id
                WHERE sr.seller_id = :id
                ORDER BY sr.created_at DESC
            ''', id=user_id)
            print(f"Debug: Reviews result: {reviews_result}")

            # Convert reviews to list of dictionaries
            reviews = []
            for review in reviews_result:
                review_dict = {
                    'rating': review.rating,
                    'review_text': review.review_text,
                    'created_at': review.created_at,
                    'reviewer_firstname': review.reviewer_firstname,
                    'reviewer_lastname': review.reviewer_lastname
                }
                reviews.append(review_dict)
                print(f"Debug: Review added: {review_dict}")

        print(f"Debug: Final data being passed to template:")
        print(f"Debug: User: {user}")
        print(f"Debug: Seller stats: {seller_stats}")
        print(f"Debug: Reviews: {reviews}")

        return render_template('public_profile.html', 
                             user=user,
                             seller_stats=seller_stats,
                             reviews=reviews)
    except Exception as e:
        print(f"Debug: Error occurred: {str(e)}")
        flash(f'Error viewing profile: {str(e)}', 'error')
        return redirect(url_for('index.index'))

@bp.route('/coupons')
@login_required
def manage_coupons():
    """Manage seller coupons."""
    # Check if user is a seller by looking at inventory
    print(f"Debug: Checking inventory for user {current_user.id}")
    inventory = app.db.execute('''
        SELECT COUNT(*) as count
        FROM Inventory
        WHERE seller_id = :id
    ''', id=current_user.id)
    
    is_seller = inventory[0].count > 0
    print(f"Debug: Inventory count: {inventory[0].count}, Is seller: {is_seller}")
    
    if not is_seller:
        flash('You need to be a seller to manage coupons.', 'warning')
        return redirect(url_for('users.account'))

    # Get active coupons for the seller with named columns
    coupon_rows = app.db.execute('''
        SELECT 
            id, 
            code, 
            discount_amount, 
            expiration_date, 
            CAST(is_active AS INTEGER) as is_active, 
            created_at
        FROM Coupons
        WHERE seller_id = :id
        ORDER BY created_at DESC
    ''', id=current_user.id)

    # Convert rows to dictionaries
    coupons = []
    for row in coupon_rows:
        coupon = {
            'id': row[0],
            'code': row[1],
            'discount_amount': row[2],
            'expiration_date': row[3],
            'is_active': row[4],
            'created_at': row[5]
        }
        coupons.append(coupon)

    # Create a user dictionary with is_seller flag
    user_dict = {
        'id': current_user.id,
        'email': current_user.email,
        'firstname': current_user.firstname,
        'lastname': current_user.lastname,
        'is_seller': is_seller
    }

    # Get today's date for the date picker
    today = datetime.now().strftime('%Y-%m-%d')

    return render_template('seller_coupons.html', user=user_dict, coupons=coupons, today=today)

@bp.route('/coupons/create', methods=['POST'])
@login_required
def create_coupon():
    """Create a new coupon."""
    # Check if user is a seller
    inventory = app.db.execute('''
        SELECT COUNT(*) as count
        FROM Inventory
        WHERE seller_id = :id
    ''', id=current_user.id)
    
    is_seller = inventory[0].count > 0
    
    if not is_seller:
        flash('You need to be a seller to manage coupons.', 'warning')
        return redirect(url_for('users.account'))

    try:
        # Get form data
        code = request.form.get('code', '').upper()  # Convert to uppercase
        discount_amount = float(request.form.get('discount_amount', 0))
        expiration_date = request.form.get('expiration_date')

        # Validate coupon code format
        if not re.match(r'^[A-Z0-9]{6,20}$', code):
            flash('Coupon code must be 6-20 characters and contain only letters and numbers.', 'danger')
            return redirect(url_for('users.manage_coupons'))

        # Validate discount amount
        if discount_amount <= 0:
            flash('Discount amount must be greater than 0.', 'danger')
            return redirect(url_for('users.manage_coupons'))

        # Convert date string to datetime (set time to end of day)
        expiration_datetime = datetime.strptime(expiration_date, '%Y-%m-%d')
        expiration_datetime = expiration_datetime.replace(hour=23, minute=59, second=59)

        if expiration_datetime <= datetime.now():
            flash('Expiration date must be in the future.', 'danger')
            return redirect(url_for('users.manage_coupons'))

        # Create coupon
        app.db.execute('''
            INSERT INTO Coupons (seller_id, code, discount_amount, expiration_date)
            VALUES (:seller_id, :code, :discount_amount, :expiration_date)
        ''', seller_id=current_user.id, code=code, discount_amount=discount_amount, 
             expiration_date=expiration_datetime)

        flash('Coupon created successfully!', 'success')
        return redirect(url_for('users.manage_coupons'))

    except Exception as e:
        flash(f'Error creating coupon: {str(e)}', 'danger')
        return redirect(url_for('users.manage_coupons'))

@bp.route('/coupons/<int:coupon_id>/deactivate', methods=['POST'])
@login_required
def deactivate_coupon(coupon_id):
    """Deactivate a coupon."""
    # Check if user is a seller
    inventory = app.db.execute('''
        SELECT COUNT(*) as count
        FROM Inventory
        WHERE seller_id = :id
    ''', id=current_user.id)
    
    is_seller = inventory[0].count > 0
    
    if not is_seller:
        flash('You need to be a seller to manage coupons.', 'warning')
        return redirect(url_for('users.account'))

    try:
        # Verify coupon belongs to seller
        coupon = app.db.execute('''
            SELECT id FROM Coupons 
            WHERE id = :coupon_id AND seller_id = :seller_id
        ''', coupon_id=coupon_id, seller_id=current_user.id)

        if not coupon:
            flash('Coupon not found or unauthorized.', 'danger')
            return redirect(url_for('users.manage_coupons'))

        # Deactivate coupon
        app.db.execute('''
            UPDATE Coupons 
            SET is_active = FALSE 
            WHERE id = :coupon_id
        ''', coupon_id=coupon_id)

        flash('Coupon deactivated successfully.', 'success')
        return redirect(url_for('users.manage_coupons'))

    except Exception as e:
        flash(f'Error deactivating coupon: {str(e)}', 'danger')
        return redirect(url_for('users.manage_coupons'))
