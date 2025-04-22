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

from .models.user import User


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
        # Retrieve form data
        new_firstname = request.form.get('firstname')
        new_lastname = request.form.get('lastname')
        new_email = request.form.get('email')
        new_password=request.form.get('password')
        new_address = request.form.get('address')
        new_balance = request.form.get('balance')
        new_balance = float(new_balance) if new_balance else 0.00

        # Validation: prevent negative balance
        if new_balance < 0:
            flash("Balance cannot be negative.", "danger")
            return redirect(url_for('users.account'))
        
        # Update the user details in the database
        try:
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

        user_details = app.db.execute('''
        SELECT id, email, firstname, lastname, address, balance
        FROM Users
        WHERE id = :id
    ''', id=current_user.id)[0]

        return render_template('profile.html', user=user_details)
        #return redirect(url_for('users.account'))

    # Fetch the current user details
    user_details = app.db.execute('''
        SELECT id, email, firstname, lastname, address, balance
        FROM Users
        WHERE id = :id
    ''', id=current_user.id)[0]

    return render_template('profile.html', user=user_details)

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
