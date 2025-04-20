from flask import render_template, request
from flask_login import current_user, login_required
from flask import redirect, url_for, flash, abort
from datetime import datetime

from .models.product_review import ProductReview
from .models.seller_review import SellerReview

from flask import Blueprint
bp = Blueprint('review', __name__, url_prefix='/reviews')


@bp.route('/', methods=['GET'])
@login_required
def review_history_all():
    # Check which tab is active
    review_type = request.args.get("review_type", "product")

    # Load both but only show one depending on tab (for fast switching)
    product_reviews = ProductReview.get_by_user(current_user.id)
    seller_reviews = SellerReview.get_by_user(current_user.id)

    return render_template('review_history_all.html',
                           review_type=review_type,
                           product_reviews=product_reviews,
                           seller_reviews=seller_reviews)
            
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

