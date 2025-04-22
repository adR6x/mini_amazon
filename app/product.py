from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, abort
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, FloatField
from wtforms.validators import Optional, NumberRange

from .models.product import Product
from .models.product_review import ProductReview

bp = Blueprint('product', __name__)


class FilterForm(FlaskForm):
    review = SelectField(
        "Review Rating",
        choices=[('', "- Stars -"), ('1', "1 Star"), ('2', "2 Stars"),
                 ('3', "3 Stars"), ('4', "4 Stars"), ('5', "5 Stars")],
        validators=[Optional()],
        default=''
    )
    min_price = FloatField(
        "Min Price",
        validators=[Optional(), NumberRange(min=0)],
        default=None
    )
    max_price = FloatField(
        "Max Price",
        validators=[Optional(), NumberRange(min=0)],
        default=None
    )
    most_exp = IntegerField(
        "Most Expensive (top N)",
        validators=[Optional(), NumberRange(min=1)],
        default=None
    )
    submit = SubmitField("Apply Filters")


@bp.route('/product_all', methods=['GET', 'POST'])
def product_all():
    form = FilterForm()
    if form.validate_on_submit():
        return redirect(url_for(
            'product.product_filtered',
            review=form.review.data or None,
            min_price=form.min_price.data,
            max_price=form.max_price.data,
            most_exp=form.most_exp.data
        ))

    products = Product.get_all_rnd5()
    return render_template(
        'product_all.html',
        avail_products=products,
        form=form
    )


@bp.route('/product_all/filtered', methods=['GET'])
def product_filtered():
    form = FilterForm(csrf_enabled=False)
    # grab query params
    review    = request.args.get('review',    type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    most_exp  = request.args.get('most_exp',  type=int)

    # apply your filtering logic
    if most_exp:
        products = Product.get_filtered_top_exp(most_exp)
    else:
        products = Product.get_all_rnd5()
        # you can also handle min_price/max_price/review here

    return render_template(
        'product_all.html',
        avail_products=products,
        form=form
    )


@bp.route('/product/<int:product_id>', methods=['GET'])
@login_required
def detail(product_id):
    product = Product.get(product_id)
    if not product:
        abort(404)

    reviews = ProductReview.get_by_product(product_id)
    count   = len(reviews)
    avg     = round(sum(r.rating for r in reviews) / count, 2) if count else None

    user_rev = ProductReview.get_by_user_and_product(
        current_user.id, product_id
    )

    # sort logic
    sort = request.args.get('sort', 'date')
    if sort == 'rating':
        reviews.sort(key=lambda r: r.rating, reverse=True)
    else:
        reviews.sort(key=lambda r: r.created_at, reverse=True)

    return render_template(
        'product_detail.html',
        product=product,
        reviews=reviews,
        avg=avg,
        count=count,
        user_rev=user_rev,
        sort=sort
    )


@bp.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    # only one per user
    if ProductReview.get_by_user_and_product(current_user.id, product_id):
        flash("You've already reviewed this product.", 'warning')
    else:
        rating = int(request.form['rating'])
        text   = request.form.get('review_text', '').strip()
        ProductReview.create(product_id, current_user.id, rating, text)
        flash('Review submitted!', 'success')

    return redirect(url_for('product.detail', product_id=product_id))
