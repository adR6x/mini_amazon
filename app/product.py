from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, abort
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, FloatField, StringField
from wtforms.validators import DataRequired, NumberRange, Optional
import datetime

from .models.product import Product, Category
from .models.purchase import Purchase

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

def form_validate(form):
    review=form.review.data 
    min_price=form.min_price.data
    max_price=form.max_price.data
    most_exp=form.most_exp.data
    
    if all(v is not None for v in [review, min_price, max_price, most_exp]):
        return Product.get_filtered_all(review, min_price, max_price, most_exp)

    elif most_exp is not None:
        return Product.get_filtered_top_exp(most_exp)
    
    else:
        return Product.get_all_rnd5()
    
class SearchForm(FlaskForm):
    query = StringField("Search", validators=[Optional()])
    submit = SubmitField("Search")    

def search_validate(form):
    query = form.query.data
    if query:
        products = Product.get_by_search(query)
        page_heading="Search results for " + query
        return products, page_heading
    else:
        page_heading="Oops! You didn't search for anything 🙃"
        return Product.get_all_rnd5(), page_heading
    
@bp.route('/product_all', methods=['GET','POST'])
def product_all():
    
    ## Catagories
    unique_cat = Category.get_unique()

    products = Product.get_all_rnd5()        
    page_heading="All Products"
    
    filter_form = FilterForm()
    if filter_form.validate_on_submit():
        products = form_validate(filter_form)
        
    search_form = SearchForm()
    if search_form.validate_on_submit():
        products = search_validate(search_form)[0]
        page_heading = search_validate(search_form)[1]    
        
    return render_template('product_all.html',
                           avail_products=products,
                           br_category=unique_cat,
                           form=filter_form,
                           search_form=search_form,
                           page_heading=page_heading)
    

@bp.route('/product/category', methods=['GET','POST'])
def by_category():
    
    category_id = request.args.get('category_id')
    category_name = request.args.get('category_name')
    
    ## Catagories
    unique_cat = Category.get_unique()

    products = Product.get_by_cat(category_id)
    
    page_heading="Category: "+category_name        
    
    filter_form = FilterForm()
    if filter_form.validate_on_submit():
        products = form_validate(filter_form)
        
    search_form = SearchForm()
    if search_form.validate_on_submit():
        products = search_validate(search_form)[0]
        page_heading = search_validate(search_form)[1]   
        
    return render_template('product_all.html',
                           avail_products=products,
                           br_category=unique_cat,
                           form=filter_form,
                           search_form=search_form,
                           page_heading=page_heading) 