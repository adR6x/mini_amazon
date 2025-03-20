from flask import Blueprint, jsonify
from app.models.inventory import Inventory

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/seller/<int:seller_id>/inventory', methods=['GET'])
def get_seller_inventory(seller_id):
    inventory = Inventory.get_by_seller(seller_id)
    if not inventory:
        return jsonify({"message": "No products found for this seller"}), 404

    return jsonify([
        {
            "seller_id": item.seller_id,
            "product_id": item.product_id,
            "product_name": item.product_name,
            "quantity_available": item.quantity_available,
            "price": float(item.price)
        }
        for item in inventory
    ]), 200
