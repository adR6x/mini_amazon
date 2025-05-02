from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from datetime import datetime
from math import ceil

from .models.product_review import ProductReview
from .models.seller_review import SellerReview
from flask import Blueprint

bp = Blueprint('review', __name__, url_prefix='/reviews')

class Pagination:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = ceil(total / per_page) if per_page else 0

@bp.route('/', methods=['GET'])
@login_required
def review_history_all():
    review_type = request.args.get('review_type', 'product')
    # Pagination parameters
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get('per_page', 5))
    except ValueError:
        per_page = 5
    per_page = per_page if per_page in (5, 10, 20) else 5

    # Load all reviews
    all_product = ProductReview.get_by_user(current_user.id)
    all_seller = SellerReview.get_by_user(current_user.id)

    # Slice for pagination
    def paginate_list(full_list):
        total = len(full_list)
        start = (page - 1) * per_page
        end = start + per_page
        items = full_list[start:end]
        return Pagination(items, page, per_page, total)

    product_reviews = paginate_list(all_product)
    seller_reviews = paginate_list(all_seller)

    return render_template(
        'review_history_all.html',
        review_type=review_type,
        product_reviews=product_reviews,
        seller_reviews=seller_reviews
    )

@bp.route('/product/<int:review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product_review(review_id):
    review = ProductReview.get_by_id(review_id)
    if not review or review.reviewer_id != current_user.id:
        abort(404)
    if request.method == 'POST':
        rating = int(request.form['rating'])
        review_text = request.form.get('review_text')
        ProductReview.update(review_id, rating=rating, review_text=review_text)
        flash('Product review updated.', 'success')
        return redirect(url_for('review.review_history_all', review_type='product'))
    return render_template('edit_product_review.html', review=review)

@bp.route('/product/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_product_review(review_id):
    review = ProductReview.get_by_id(review_id)
    if not review or review.reviewer_id != current_user.id:
        abort(404)
    ProductReview.delete(review_id)
    flash('Product review deleted.', 'warning')
    return redirect(url_for('review.review_history_all', review_type='product'))

@bp.route('/seller/<int:seller_review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_seller_review(seller_review_id):
    review = SellerReview.get_by_id(seller_review_id)
    if not review or review.reviewer_id != current_user.id:
        abort(404)
    if request.method == 'POST':
        rating = int(request.form['rating'])
        review_text = request.form.get('review_text')
        SellerReview.update(seller_review_id, rating=rating, review_text=review_text)
        flash('Seller review updated.', 'success')
        return redirect(url_for('review.review_history_all', review_type='seller'))
    return render_template('edit_seller_review.html', review=review)

@bp.route('/seller/<int:seller_review_id>/delete', methods=['POST'])
@login_required
def delete_seller_review(seller_review_id):
    review = SellerReview.get_by_id(seller_review_id)
    if not review or review.reviewer_id != current_user.id:
        abort(404)
    SellerReview.delete(seller_review_id)
    flash('Seller review deleted.', 'warning')
    return redirect(url_for('review.review_history_all', review_type='seller'))


@bp.route('/seller/<int:seller_id>/create', methods=['GET', 'POST'])
@login_required
def create_seller_review(seller_id):
    # 1) block GET if already reviewed
    existing = SellerReview.get_by_user_and_seller(current_user.id, seller_id)
    if existing:
        flash('You’ve already submitted a review for this seller.', 'info')
        return redirect(url_for('review.review_history_all', review_type='seller'))

    if request.method == 'POST':
        # parse & validate rating
        try:
            rating = int(request.form['rating'])
            if not 1 <= rating <= 5:
                raise ValueError
        except (KeyError, ValueError):
            flash('Please provide a rating between 1 and 5.', 'danger')
            return redirect(url_for('review.create_seller_review', seller_id=seller_id))

        review_text = request.form.get('review_text')
        image_url   = request.form.get('image_url')

        # create and persist
        SellerReview.create(
            seller_id=seller_id,
            reviewer_id=current_user.id,
            rating=rating,
            review_text=review_text,
            image_url=image_url
        )
        flash('Seller review submitted.', 'success')
        return redirect(url_for('review.review_history_all', review_type='seller'))

    # GET → render blank form
    return render_template('create_seller_review.html', seller_id=seller_id)

@bp.route('/seller/<int:seller_id>/reviews', methods=['GET'])
def seller_reviews(seller_id):
    reviews = SellerReview.get_by_seller(seller_id)
    return render_template('seller_reviews.html',
                           reviews=reviews,
                           seller_id=seller_id)
