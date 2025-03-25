from flask import render_template, request
from flask_login import current_user, login_required
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
