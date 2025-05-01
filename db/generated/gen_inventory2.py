import csv
from faker import Faker
from datetime import datetime
import random

fake = Faker()

def generate_inventory_records_from_products():
    # Read products to get product IDs, seller IDs, and prices
    products = []
    with open('../generated/Products.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            try:
                product_id = int(row[0].strip('"'))
                seller_id = int(row[1].strip('"'))
                price = float(row[-1].strip('"'))
                products.append((product_id, seller_id, price))
            except (ValueError, IndexError):
                continue

    # Read existing inventory to get the next ID
    try:
        with open('../generated/Inventory.csv', 'r') as f:
            reader = csv.reader(f)
            last_id = max(int(row[0].strip('"')) for row in reader)
    except FileNotFoundError:
        last_id = 0

    # Generate new inventory records
    records = []
    for i, (product_id, seller_id, price) in enumerate(products):
        if (product_id == 38):
            print("the price of product id 3:", price)
        quantity = random.randint(1, 100)
        created_at = fake.date_time_between(start_date='-1y', end_date='now')
        updated_at = created_at  # Same timestamp for created_at and updated_at

        record = [
            str(last_id + i + 1),  # id
            str(seller_id),        # seller_id
            str(product_id),       # product_id
            str(quantity),         # quantity
            str(price),            # price
            created_at.strftime('%Y-%m-%d %H:%M:%S'),  # created_at
            updated_at.strftime('%Y-%m-%d %H:%M:%S')   # updated_at
        ]
        records.append([f'"{value}"' for value in record])

    # Write to Inventory.csv
    with open('../generated/Inventory.csv', 'a', newline='') as f:
        for record in records:
            f.write(','.join(record) + '\n')

    print(f"Generated {len(records)} inventory records from products.")

if __name__ == "__main__":
    generate_inventory_records_from_products()