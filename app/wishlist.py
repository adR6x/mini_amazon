from flask_login import current_user
import datetime
from flask import jsonify
from flask import redirect, url_for

from .models.wishlist import WishlistItem

from flask import Blueprint
bp = Blueprint('wishlist', __name__)

import humanize
from humanize import naturaltime

def humanize_time(dt):
    return naturaltime(datetime.datetime.now() - dt)


@bp.route('/wishlist')
def wish_list():
    if not current_user.is_authenticated:
        return jsonify({"error": "Not logged in"}), 404
    
    items=WishlistItem.get_all_by_uid_since(
        current_user.id,
        datetime.datetime(1980, 9, 14, 0, 0, 0)
    )

    return render_template(
        'wishlist.html',
        items=items,
        humanize_time=humanize_time
    )

@bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
def wish_list_add(product_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Not logged in"}), 404
    new_item=WishlistItem.add(current_user.id, product_id)
    return redirect(url_for('wishlist.wish_list'))


