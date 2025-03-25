from flask import render_template
from flask_login import current_user
from flask import jsonify
import datetime

from .models.product import Product
from .models.purchase import Purchase
from flask import redirect, url_for
from .models.wishlist import WishlistItem
from humanize import naturaltime

def humanize_time(dt):
    return naturaltime(datetime.datetime.now() - dt)


from flask import Blueprint
bp = Blueprint('wishlist', __name__)


@bp.route('/wishlist')
def wishlist():
    # get all available products in wishlist:
    items = WishlistItem.get_all_by_uid_since(current_user.id, datetime.datetime(1980, 9, 14, 0, 0, 0))

    if current_user.is_authenticated:
        return render_template('wishlist.html',
                       items=items,
                       humanize_time=humanize_time)

    else:
       return jsonfiy({}), 404

@bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
def wishlist_add(product_id):
    WishlistItem.add_to_wishlist(current_user.id, product_id)
    return redirect(url_for('wishlist.wishlist'))
