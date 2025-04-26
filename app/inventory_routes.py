from flask import Blueprint, jsonify, flash, redirect, url_for
from app.models.inventory import Inventory
from flask_login import current_user
from flask import render_template, request


inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory', methods=['GET'])
def inventory_page():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)
    category_id = request.args.get('category', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    items_per_page = 9

    categories = Inventory.get_all_categories()

    total_items, inventory_items = Inventory.filter_inventory(
        current_user.id, search_query, category_id, min_price, max_price, page, items_per_page
    )

    total_pages = (total_items + items_per_page - 1) // items_per_page

    return render_template(
        'inventory.html', inventory_items=inventory_items, page=page, total_pages=total_pages,
        search_query=search_query, category_id=category_id, min_price=min_price, max_price=max_price,
        categories=categories
    )

@inventory_bp.route('/inventory/add', methods=['POST'])
def add_inventory():
    from flask_login import current_user
    data = request.get_json()
    short_name = data.get("short_name")
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


@inventory_bp.route('/inventory/item/<int:product_id>', methods=['GET'])
def inventory_detail(product_id):
    item = Inventory.get_inventory_detail(product_id)

    categories = Inventory.get_all_categories()

    if item:
        return render_template('inventory_detail.html', item=item, categories=categories)
    else:
        return "Item not found", 404



@inventory_bp.route('/inventory/item/<int:product_id>/update', methods=['POST'])
def update_inventory_item(product_id):
    print("update inventory item")
    data = request.json
    seller_id = current_user.id  # Assuming you have access to the current user's ID

    try:
        # Update each field
        for field, value in data.items():
            # print(field, value)
            Inventory.update_field(seller_id, product_id, field, value)
        return jsonify(success=True, message="Inventory item updated successfully.")
    except Exception as e:
        print(f"Error updating inventory item: {e}")
        return jsonify(success=False, message="Failed to update inventory item.")

@inventory_bp.route('/inventory/item/<int:product_id>/delete', methods=['POST'])
def delete_inventory_item(product_id):
    seller_id = current_user.id

    try:
        Inventory.delete_item(seller_id, product_id)
        print("deleting item")
        print(seller_id)
        print(product_id)
        flash('Inventory item deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting inventory item: {e}', 'danger')

    return redirect(url_for('inventory.inventory_page'))