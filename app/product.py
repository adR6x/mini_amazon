from flask import render_template
from flask_login import current_user
import datetime

from .models.product import Product
from .models.purchase import Purchase

from flask import Blueprint
bp = Blueprint('product', __name__)


@bp.route('/product_all', methods=['GET', 'POST'])
def product_all():
    return render_template('product_all.html')
