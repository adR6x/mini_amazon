from flask import render_template, redirect, url_for, request, jsonify
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, NumberRange, Optional
import datetime

from .models.product import Product
from .models.purchase import Purchase

from flask import Blueprint
bp = Blueprint('product', __name__)

class FilterForm(FlaskForm):
    review = SelectField(
        "Review Rating",
        choices=[(None, "- Stars -"), (1, "1 Star"), (2, "2 Stars"), (3, "3 Stars"), (4, "4 Stars"), (5, "5 Stars")],
        validators=[Optional()],
        default=None
    )
    min_price = FloatField("Min Price", validators=[Optional(), NumberRange(min=0)], default=None)
    max_price = FloatField("Max Price", validators=[Optional(), NumberRange(min=0)], default=None)
    most_exp = IntegerField("Most Expensive", validators=[Optional(), NumberRange(min=0)], default=None)
    submit = SubmitField("Apply Filters")


@bp.route('/product_all', methods=['GET', 'POST'])
def product_all():
    filter_form = FilterForm()
    if filter_form.validate_on_submit():
               
        return redirect(url_for('product.product_filtered',
                                # review=filter_form.review.data, 
                                # min_price=filter_form.min_price.data, 
                                # max_price=filter_form.max_price.data,
                                most_exp=filter_form.most_exp.data))
    
    products = Product.get_all_rnd5()        
    return render_template('product_all.html',
                           avail_products=products,
                        #    purchase_history=purchases,
                           form=filter_form)
    
@bp.route('/product_all/filtered', methods=['GET', 'POST'])
def product_filtered():
    filter_form = FilterForm()
    
    if request.method == "GET":
        # Extract filter parameters from query string
        # review = request.args.get("review", type=int)
        # min_price = request.args.get("min_price", type=float)
        # max_price = request.args.get("max_price", type=float)
        most_exp= request.args.get("most_exp", type=int)
        if most_exp is not None:
            products = Product.get_filtered_top_exp(most_exp)
        else:
            products = Product.get_all_rnd5()  
        # return jsonify({"review": review, "min_price": min_price, "max_price": max_price})

    elif request.method == "POST":
        
        
        if filter_form.validate_on_submit():
                    
            return redirect(url_for('product.product_filtered',
                                    review=filter_form.review.data, 
                                    min_price=filter_form.min_price.data, 
                                    max_price=filter_form.max_price.data,
                                    most_exp=filter_form.most_exp.data))
            
    return render_template('product_all.html',
                        avail_products=products,
                    #    purchase_history=purchases,
                        form=filter_form)        