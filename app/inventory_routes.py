from flask import Blueprint, jsonify
from app.models.inventory import Inventory
from flask_login import current_user
from flask import render_template, request


inventory_bp = Blueprint('inventory', __name__)

# @inventory_bp.route('/inventory_page')
# def inventory_page():
#     seller_id = current_user.id
#     inventory = Inventory.get_by_seller(seller_id)
#     # print(seller_id)
#     # print(inventory)
#     return render_template("inventory.html", inventory=inventory)

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

@inventory_bp.route('/inventory/add', methods=['POST'])
def add_inventory():
    from flask_login import current_user
    data = request.get_json()
    short_name = data.get("short_name")
    print(short_name)
    description = data.get("description")
    image_url = data.get("image_url")
    price = data.get("price")
    category_id = data.get("category_id")
    quantity_available = data.get("quantity_available")

    # Check if product already exists
    if Inventory.product_exists(current_user.id, short_name):
        return jsonify({"error": "Product already exists"}), 400

    # Add new product
    product_id = Inventory.add_product(current_user.id, category_id, short_name, description, image_url, price)
    if not product_id:
        return jsonify({"error": "Failed to add product"}), 500

    # Add new inventory
    inventory_id = Inventory.add_inventory(current_user.id, product_id, quantity_available, price)
    if not inventory_id:
        return jsonify({"error": "Failed to add inventory"}), 500

    return jsonify({"success": True, "product_id": product_id, "inventory_id": inventory_id}), 200

@inventory_bp.route('/inventory/add', methods=['GET'])
def show_add_inventory_form():
    categories = Inventory.get_all_categories()
    return render_template('inventory_add.html', categories=categories)


@inventory_bp.route('/inventory', methods=['GET'])
def inventory_page():
    page = request.args.get('page', 1, type=int)
    items_per_page = 9
    total_items = Inventory.get_total_inventory_count()
    total_pages = (total_items + items_per_page - 1) // items_per_page
    print(page)
    print(items_per_page)
    inventory_items = Inventory.get_inventory_items(page, items_per_page)
    print(inventory_items)
    
    return render_template('inventory.html', inventory_items=inventory_items, page=page, total_pages=total_pages)