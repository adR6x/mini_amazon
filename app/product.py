from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, abort
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, FloatField
from wtforms.validators import Optional, NumberRange

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


@bp.route('/product_all', methods=['GET','POST'])
def product_all():
    
    ## Catagories
    unique_cat = Category.get_unique()

    products = Product.get_all_rnd5()        
    page_heading="All Products"
    
    filter_form = FilterForm()
    if filter_form.validate_on_submit():
        review=filter_form.review.data 
        min_price=filter_form.min_price.data
        max_price=filter_form.max_price.data
        most_exp=filter_form.most_exp.data
        
        if all(v is not None for v in [review, min_price, max_price, most_exp]):
            products = Product.get_filtered_all(review, min_price, max_price, most_exp)

        elif most_exp is not None:
            products = Product.get_filtered_top_exp(most_exp)
        
        else:
            products = Product.get_all_rnd5()
        
    return render_template('product_all.html',
                           avail_products=products,
                           br_category=unique_cat,
                           form=filter_form,
                           page_heading=page_heading)
    

@bp.route('/product/category', methods=['GET','POST'])
def by_category():
    
    category_id = request.args.get('category_id')
    category_name = request.args.get('category_name')
    
    ## Catagories
    unique_cat = Category.get_unique()

    products = Product.get_all_rnd5()
    
    page_heading="Category: "+category_name        
    
    filter_form = FilterForm()
    if filter_form.validate_on_submit():
        review=filter_form.review.data 
        min_price=filter_form.min_price.data
        max_price=filter_form.max_price.data
        most_exp=filter_form.most_exp.data
        
        if all(v is not None for v in [review, min_price, max_price, most_exp]):
            products = Product.get_filtered_all(review, min_price, max_price, most_exp)

        elif most_exp is not None:
            products = Product.get_filtered_top_exp(most_exp)
        
        else:
            products = Product.get_all_rnd5()
        
    return render_template('product_all.html',
                           avail_products=products,
                           br_category=unique_cat,
                           form=filter_form,
                            page_heading=page_heading)    