from flask import render_template, redirect, url_for
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, NumberRange
import datetime
from flask import jsonify

from .models.product import Product
from .models.purchase import Purchase

from flask import Blueprint
bp = Blueprint('product', __name__)

class FilterForm(FlaskForm):
    review = SelectField(
        "Review Rating",
        choices=[(None, "- Stars -"), (1, "1 Star"), (2, "2 Stars"), (3, "3 Stars"), (4, "4 Stars"), (5, "5 Stars")]
        # coerce=int
    )
    min_price = FloatField("Min Price", default=None)
    max_price = FloatField("Max Price", default=None)
    submit = SubmitField("Apply Filters")


@bp.route('/product_all', methods=['GET', 'POST'])
def product_all():
    # get all available products for sale:
    products = Product.get_all_top5(True)
    # find the products current user has bought:
    if current_user.is_authenticated:
        purchases = Purchase.get_all_by_uid_since(
            current_user.id, datetime.datetime(1980, 9, 14, 0, 0, 0))
    else:
        purchases = None

    filter_form = FilterForm()
    # if filter_form.validate_on_submit():
    #     min_price = round(filter_form.min_price.data, 2) if filter_form.min_price.data else None
    #     max_price = round(filter_form.max_price.data, 2) if filter_form.max_price.data else None
        
    #     return redirect(url_for('product.product_filtered',
    #                             review=filter_form.review.data, 
    #                             min_price=min_price, 
    #                             max_price=max_price))
            
    return render_template('product_all.html',
                           avail_products=products,
                           purchase_history=purchases,
                           form=filter_form)
    
# @bp.route('/product_all/filtered', methods=['GET', 'POST'])
# def product_filtered():
#     # find the products current user has bought:
#     if current_user.is_authenticated:
#         purchases = Purchase.get_all_by_uid_since(
#             current_user.id, datetime.datetime(1980, 9, 14, 0, 0, 0))
#     else:
#         purchases = None

#     filter_form = FilterForm()
#     if filter_form.validate_on_submit():  
#         return jsonify({field.name: field.data for field in filter_form})

#         if (filter_form.review.data != "") and (filter_form.min_price.data is not None) and (filter_form.max_price.data is not None):
            
#             min_price=min(filter_form.min_price, filter_form.max_price)
#             max_price=max(filter_form.min_price, filter_form.max_price)
            
            
            
#             products = Product.get_filtered_top5(filter_form.review, min_price, max_price)

#             return render_template('product_all.html',
#                                 avail_products=products,
#                                 purchase_history=purchases,
#                                 form=filter_form)    