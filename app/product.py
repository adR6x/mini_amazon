from flask import render_template
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange
import datetime

from .models.product import Product
from .models.purchase import Purchase

from flask import Blueprint
bp = Blueprint('product', __name__)

class FilterForm(FlaskForm):
    review = SelectField(
        "Review Rating",
        choices=[("1", "1 Star"), ("2", "2 Stars"), ("3", "3 Stars"), ("4", "4 Stars"), ("5", "5 Stars")],
    )
    min_price = IntegerField("Min Price")
    max_price = IntegerField("Max Price")
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
    # render the page by adding information to the index.html file
    
    filter_form = FilterForm()
    
    return render_template('product_all.html',
                           avail_products=products,
                           purchase_history=purchases,
                           form=filter_form)
    
       
     