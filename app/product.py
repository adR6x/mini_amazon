from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, abort
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, FloatField, StringField
from wtforms.validators import Optional, NumberRange

from .models.product import Product, Category
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
    
    category = SelectField(
    "Category",
    validators=[Optional()],
    default=''
    )
    submit = SubmitField("Apply Filters")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category.choices = [('', "- Category -")] + [
            (str(cat.id), cat.name) for cat in Category.get_unique()
        ]
    
    submit = SubmitField("Apply Filters")
    


def form_validate(form):
    review = form.review.data
    min_price = form.min_price.data
    max_price = form.max_price.data
    most_exp = form.most_exp.data
    category = form.category.data

    products = Product.get_filtered_all(review, min_price, max_price, most_exp, category)
    page_heading = "🪄 Filtered Products"
    return products, page_heading

    # if all(v is not None for v in [review, min_price, max_price, most_exp, category]):
    #     products = Product.get_filtered_all(review, min_price, max_price, most_exp, category)
    #     page_heading = "🪄 Filtered Products"
    #     return products, page_heading
    # elif most_exp is not None:
    #     products = Product.get_filtered_top_exp(most_exp)
    #     page_heading = f"🪄 Top {most_exp} Most Expensive Products"
    #     return products, page_heading
    # elif category is not None:
    #     products = Product.get_by_cat(category)
    #     categories = [cat for cat in Category.get_unique()]
    #     selected = next((cat for cat in categories if str(cat.id) == category), None)
    #     page_heading = f"🪄 Category: {selected.name}" if selected else "Category: Unknown"
    #     return products, page_heading
    
    # else:
    #     return Product.get_all_rnd5()


class SearchForm(FlaskForm):
    query = StringField("Search", validators=[Optional()])
    submit = SubmitField("🔍")


def search_validate(form):
    query = form.query.data
    if query:
        products = Product.get_by_search(query)
        page_heading = "Search results for " + query
        return products, page_heading
    else:
        page_heading = "Oops! You didn't search for anything 🙃"
        return Product.get_all_rnd5(), page_heading


@bp.route('/product_all', methods=['GET', 'POST'])
def product_all():
    unique_cat = Category.get_unique()
    products = Product.get_all_rnd5()
    page_heading = "All Products 🛍️"

    filter_form = FilterForm(prefix="filter")
    search_form = SearchForm(prefix="search")
    
    if request.method == 'POST':
        if 'filter-submit' in request.form and filter_form.validate():
            products, page_heading = form_validate(filter_form)

        elif 'search-submit' in request.form and search_form.validate():
            products, page_heading = search_validate(search_form)
        

    return render_template(
        'product_all.html',
        avail_products=products,
        br_category=unique_cat,
        form=filter_form,
        search_form=search_form,
        page_heading=page_heading
    )


@bp.route('/product/category', methods=['GET', 'POST'])
def by_category():
    category_id = request.args.get('category_id')
    category_name = request.args.get('category_name')

    unique_cat = Category.get_unique()
    products = Product.get_by_cat(category_id)
    page_heading = "🧭 Category: " + category_name

    filter_form = FilterForm(prefix="filter")
    search_form = SearchForm(prefix="search")
    
    if request.method == 'POST':
        if 'filter-submit' in request.form and filter_form.validate():
            products, page_heading = form_validate(filter_form)

        elif 'search-submit' in request.form and search_form.validate():
            products, page_heading = search_validate(search_form)

    return render_template(
        'product_all.html',
        avail_products=products,
        br_category=unique_cat,
        form=filter_form,
        search_form=search_form,
        page_heading=page_heading
    )


@bp.route('/product/<int:product_id>', methods=['GET'])
def detail(product_id):
    product = Product.get(product_id)
    if not product:
        abort(404)

    # Fetch all reviews (each has .upvotes_count)
    reviews = ProductReview.get_by_product(product_id)
    count   = len(reviews)
    avg     = round(sum(r.rating for r in reviews) / count, 2) if count else None

    # If the user is logged in, fetch their own review for edit/delete UI
    if current_user.is_authenticated:
        user_rev = ProductReview.get_by_user_and_product(
            current_user.id, product_id
        )
    else:
        user_rev = None
    helpful_reviews = [r for r in reviews if r.upvotes_count > 0]
    top3 = sorted(
        helpful_reviews,
        key=lambda r: r.upvotes_count,
        reverse=True
    )[:3]
    rest = [r for r in reviews if r not in top3]
    rest.sort(key=lambda r: r.created_at, reverse=True)

    ordered_reviews = top3 + rest

    return render_template(
        'product_detail.html',
        product=product,
        reviews=ordered_reviews,
        avg=avg,
        count=count,
        user_rev=user_rev
    )



@bp.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    # only one review per user
    if ProductReview.get_by_user_and_product(current_user.id, product_id):
        flash("You've already reviewed this product.", 'warning')
    else:
        rating = int(request.form['rating'])
        text = request.form.get('review_text', '').strip()
        ProductReview.create(product_id, current_user.id, rating, text)
        flash('Review submitted!', 'success')

    return redirect(url_for('product.detail', product_id=product_id))

@bp.route('/review/<int:review_id>/upvote', methods=['POST'])
@login_required
def upvote_review(review_id):
    ProductReview.upvote(review_id, current_user.id)
    flash('Marked as helpful 👍', 'success')
    # redirect back to the product detail
    return redirect(request.referrer or url_for('product.product_all'))

@bp.route('/review/<int:review_id>/remove_upvote', methods=['POST'])
@login_required
def remove_upvote_review(review_id):
    ProductReview.remove_upvote(review_id, current_user.id)
    flash('Removed your vote', 'info')
    return redirect(request.referrer or url_for('product.product_all'))
