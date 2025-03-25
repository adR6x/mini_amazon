from flask import Blueprint, jsonify
from app.models.inventory import Inventory
from flask_login import current_user
from flask import render_template, request


inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory_page')

def inventory_page():
    seller_id = current_user.id
    inventory = Inventory.get_by_seller(seller_id)
    # print(seller_id)
    # print(inventory)
    return render_template("inventory.html", inventory=inventory)