import csv
from faker import Faker
from datetime import datetime, timedelta
import random

fake = Faker()

def get_valid_user_ids():
    with open('../data/Users.csv', 'r') as f:
        reader = csv.reader(f)
        return [int(row[0].strip('"')) for row in reader]

def fix_inventory_file(valid_user_ids):
    """Fix the existing inventory file to use only valid user IDs."""
    rows = []
    with open('../data/Inventory.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            # Replace invalid seller_id with a random valid one
            row_data = [val.strip('"') for val in row]
            seller_id = int(row_data[2])
            if seller_id not in valid_user_ids:
                row_data[2] = str(random.choice(valid_user_ids))
            rows.append([f'"{val}"' for val in row_data])
    
    with open('../data/Inventory.csv', 'w', newline='') as f:
        for row in rows:
            f.write(','.join(row) + '\n')

def generate_inventory_records(num_records, seller_id):
    # Get valid user IDs
    valid_user_ids = get_valid_user_ids()
    
    # Fix existing inventory
    fix_inventory_file(valid_user_ids)
    
    # Read existing inventory to get the next ID
    try:
        with open('../data/Inventory.csv', 'r') as f:
            reader = csv.reader(f)
            last_id = max(int(row[0].strip('"')) for row in reader)
    except FileNotFoundError:
        last_id = 0

    # Read products to get valid product IDs and prices
    products = {}
    with open('../data/Products.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            try:
                products[int(row[0].strip('"'))] = float(row[-1].strip('"'))  # product_id -> price
            except (ValueError, IndexError):
                continue

    # Generate new records
    records = []
    for i in range(num_records):
        # Randomly select a product ID from existing products
        product_id = random.choice(list(products.keys()))
        quantity = random.randint(1, 100)
        # Generate a price within 80-120% of the product's base price
        base_price = products[product_id]
        price = round(base_price * random.uniform(0.8, 1.2), 2)
        created_at = fake.date_time_between(start_date='-1y', end_date='now')
        updated_at = created_at + timedelta(days=random.randint(0, 30))
        
        record = [
            str(last_id + i + 1),  # id
            str(product_id),       # product_id
            str(seller_id),        # seller_id
            str(quantity),         # quantity
            str(price),           # price
            created_at.strftime('%Y-%m-%d %H:%M:%S'),  # created_at
            updated_at.strftime('%Y-%m-%d %H:%M:%S')   # updated_at
        ]
        records.append([f'"{value}"' for value in record])

    # Write to CSV
    with open('../data/Inventory.csv', 'a', newline='') as f:
        for record in records:
            f.write(','.join(record) + '\n')

    print(f"Generated {num_records} inventory records for seller_id={seller_id}")

if __name__ == "__main__":
    generate_inventory_records(40, 100) 