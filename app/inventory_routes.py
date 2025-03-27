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

@inventory_bp.route('/inventory/item/<int:product_id>')
def inventory_detail(product_id):
    from flask_login import current_user
    inventory = Inventory.get_by_seller(current_user.id)
    item = next((i for i in inventory if i.product_id == product_id), None)
    
    if not item:
        return "Item not found", 404
    
    return render_template("inventory_detail.html", item=item)


@inventory_bp.route('/inventory/item/<int:product_id>/update', methods=['POST'])
def update_inventory_field(product_id):
    from flask_login import current_user
    data = request.get_json()
    field = data.get("field")
    value = data.get("value")

    try:
        if field == "quantity_available":
            value = int(value)
        elif field == "price":
            value = float(value)
        else:
            return jsonify({"error": "Invalid field"}), 400
    except ValueError:
        return jsonify({"error": "Invalid value format"}), 400

    result = Inventory.update_field(current_user.id, product_id, field, value)
    if not result:
        return jsonify({"error": "Update failed"}), 400

    return jsonify({"success": True}), 200

