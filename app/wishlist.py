from flask import render_template
from flask_login import current_user
from flask import jsonify
import datetime

from .models.product import Product
from .models.purchase import Purchase
from .models.wishlist import WishlistItem

from flask import Blueprint
bp = Blueprint('wishlist', __name__)


@bp.route('/wishlist')
def wishlist():
    # get all available products in wishlist:
    items = WishlistItem.get_all_by_uid_since(current_user.id, datetime.datetime(1980, 9, 14, 0, 0, 0))

    if current_user.is_authenticated:
        return jsonify([item.__dict__ for item in items])
    else:
       return jsonfiy({}), 404