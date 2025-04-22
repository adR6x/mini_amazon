from werkzeug.security import generate_password_hash
import csv
from faker import Faker
import requests
from bs4 import BeautifulSoup

# Helper to fetch a 200x200 image URL from Bing Images
def get_bing_square_image(query):
    search_url = f"https://www.bing.com/images/search?q={query+' product'}&qft=+filterui:imagesize-custom_1500_1500&form=HDRSC2"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/110.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        return "Failed to fetch results"

    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.select("img.mimg")

    if img_tags:
        return img_tags[0].get("src")
    return "No image found"

# Modified quantities
TOKEN_USER_ID = 100  # test user ID
num_users = 100
num_products = 600
num_purchases = 200
NUM_PRODUCT_REVIEWS = 1200
NUM_SELLER_REVIEWS = 300

# Extra test-user-specific data
EXTRA_TEST_USER_PURCHASES = 50
EXTRA_TEST_USER_PRODUCT_REVIEWS = 50
EXTRA_TEST_USER_SELLER_REVIEWS_BY = 20
EXTRA_TEST_USER_SELLER_REVIEWS_FOR = 20

Faker.seed(0)
fake = Faker()

def get_csv_writer(f):
    return csv.writer(f, dialect='unix')

def gen_users(num_users):
    with open('Users.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Users...', end=' ', flush=True)
        for uid in range(num_users + 1):  # +1 to include user 100
            if uid % 10 == 0:
                print(f'{uid}', end=' ', flush=True)
            if uid == 100:
                email = "test@test.com"
                password = generate_password_hash("test")
                firstname = "Test"
                lastname = "User"
                address = "100 Test St, Test City, TS 12345"
                balance = 15000.00
            else:
                profile = fake.profile()
                email = profile['mail']
                plain_password = f'pass{uid}'
                password = generate_password_hash(plain_password)
                name_components = profile['name'].split(' ')
                firstname = name_components[0]
                lastname = name_components[-1]
                address = f"{fake.street_address()}, {fake.city()}, {fake.state_abbr()} {fake.zipcode()}"
                balance = round(fake.random.uniform(0, 5000), 2)
            writer.writerow([uid, email, password, firstname, lastname, address, balance])
        print(f'{num_users + 1} generated')
    return

def gen_products(num_products, num_users):
    available_pids = []
    with open('Products.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Products...', end=' ', flush=True)
        for pid in range(num_products):
            if pid % 100 == 0:
                print(f'{pid}', end=' ', flush=True)
            seller_id = fake.random_int(min=0, max=num_users-1)
            category_id = fake.random_int(min=1, max=3)
            name = fake.sentence(nb_words=4)[:-1]
            description = fake.paragraph(nb_sentences=1, variable_nb_sentences=False)[:-1]
            image_url = get_bing_square_image(name)
            price = round(fake.random.uniform(1, 500), 2)
            if fake.boolean(chance_of_getting_true=50):
                available_pids.append(pid)
            writer.writerow([pid, seller_id, category_id, name, description, image_url, price])
        print(f'{num_products} generated; {len(available_pids)} available')
    return available_pids

def gen_inventory(num_products):
    # First, read all product-seller mappings into memory
    product_sellers = {}
    with open('Products.csv', 'r') as pf:
        reader = csv.reader(pf)
        for row in reader:
            product_sellers[int(row[0])] = int(row[1])

    with open('Inventory.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Inventory...', end=' ', flush=True)
        
        # First, assign some products specifically to user_id 100
        test_user_products = 50  # Number of products to assign to test user
        test_user_products_assigned = 0
        
        for pid in range(num_products):
            if pid % 100 == 0:
                print(f'{pid}', end=' ', flush=True)
            
            if pid in product_sellers:
                # Assign first 50 products to user_id 100
                if test_user_products_assigned < test_user_products:
                    seller_id = 100
                    test_user_products_assigned += 1
                else:
                    seller_id = product_sellers[pid]
                
                quantity = fake.random_int(min=1, max=100)
                price = round(fake.random.uniform(1, 500), 2)
                created_at = fake.date_time()
                writer.writerow([pid+1, seller_id, pid, quantity, price, created_at, created_at])
        
        print(f'{num_products} inventory records generated')
        print(f'Assigned {test_user_products_assigned} products to test user (user_id 100)')
    return

def gen_purchases(num_purchases, available_pids, num_users):
    with open('Purchases.csv', 'w') as f:
        writer = get_csv_writer(f)
        print('Purchases...', end=' ', flush=True)
        for id in range(num_purchases):
            if id % 100 == 0:
                print(f'{id}', end=' ', flush=True)
            uid = fake.random_int(min=0, max=num_users-1)
            pid = fake.random_element(elements=available_pids)
            time_purchased = fake.date_time()
            writer.writerow([id, uid, pid, time_purchased])
        print(f'{num_purchases} generated')
    return

def gen_user_purchases(user_id, num_purchases, available_pids):
    with open('Purchases.csv', 'a') as f:
        writer = get_csv_writer(f)
        print(f'Generating {num_purchases} purchases for user {user_id}...', end=' ', flush=True)
        
        # Get product prices to ensure we stay under budget
        product_prices = {}
        with open('Products.csv', 'r') as pf:
            reader = csv.reader(pf)
            for row in reader:
                product_prices[int(row[0])] = float(row[6])  # price is in column 6
        
        total_spent = 0
        max_budget = 50000  # Increased budget to allow for more purchases
        
        for id in range(num_purchases):
            # Get a random product that won't exceed our budget
            remaining_budget = max_budget - total_spent
            available_products = [pid for pid in available_pids if product_prices[pid] <= remaining_budget]
            
            if not available_products:
                print(f"\nWarning: Cannot add more purchases without exceeding budget. Added {id} purchases.")
                break
                
            # Generate 1-3 items per order
            items_in_order = fake.random_int(min=1, max=3)
            order_total = 0
            
            for item in range(items_in_order):
                pid = fake.random_element(elements=available_products)
                time_purchased = fake.date_time()
                writer.writerow([id + 200, user_id, pid, time_purchased])
                order_total += product_prices[pid]
            
            total_spent += order_total
            
        print(f'{num_purchases} orders generated, total spent: ${total_spent:.2f}')
    return

def gen_seller_orders(num_orders, seller_id, available_pids):
    """Generate orders where the specified user is the seller"""
    # Clear existing Order_Items.csv
    with open('Order_Items.csv', 'w') as f:
        pass

    with open('Orders.csv', 'w') as f:
        writer = get_csv_writer(f)
        print(f'Generating {num_orders} orders for seller {seller_id}...', end=' ', flush=True)
        
        # Get product prices and seller info
        product_info = {}
        with open('Products.csv', 'r') as pf:
            reader = csv.reader(pf)
            for row in reader:
                product_info[int(row[0])] = {
                    'price': float(row[6]),
                    'seller_id': int(row[1])
                }
        
        # Get inventory info
        inventory_info = {}
        with open('Inventory.csv', 'r') as inf:
            reader = csv.reader(inf)
            for row in reader:
                if int(row[1]) == seller_id:  # Only consider seller's inventory
                    inventory_info[int(row[2])] = {
                        'quantity': int(row[3]),
                        'price': float(row[4])
                    }
        
        # Generate orders
        order_id = 1
        order_item_id = 1
        
        for _ in range(num_orders):
            # Random buyer (not the seller)
            buyer_id = fake.random_int(min=0, max=99)  # Exclude seller_id 100
            
            # Create 1-3 order items per order
            num_items = fake.random_int(min=1, max=3)
            order_items = []
            total_amount = 0
            
            for _ in range(num_items):
                # Pick a product from seller's inventory
                product_id = fake.random_element(elements=list(inventory_info.keys()))
                quantity = fake.random_int(min=1, max=min(5, inventory_info[product_id]['quantity']))
                unit_price = inventory_info[product_id]['price']
                total_amount += quantity * unit_price
                
                order_items.append({
                    'id': order_item_id,
                    'product_id': product_id,
                    'quantity': quantity,
                    'unit_price': unit_price
                })
                order_item_id += 1
            
            # Write order
            order_date = fake.date_time().strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([
                order_id,
                buyer_id,
                round(total_amount, 2),
                order_date,
                'pending',
                order_date
            ])
            
            # Write order items
            with open('Order_Items.csv', 'a') as oif:
                oi_writer = get_csv_writer(oif)
                for item in order_items:
                    oi_writer.writerow([
                        item['id'],
                        order_id,
                        item['product_id'],
                        seller_id,
                        int(item['quantity']),  # Ensure integer
                        round(item['unit_price'], 2),
                        'pending',
                        order_date  # Use the same date as the order
                    ])
            
            order_id += 1
        
        print(f'{num_orders} orders generated for seller {seller_id}')
    return

def gen_product_reviews(count, available):
    used = set()
    with open('Product_Reviews.csv', 'w') as f:
        writer = get_csv_writer(f)
        rid = 0
        while rid < count:
            rev = fake.random_int(0, num_users)
            pid = fake.random_element(available)
            if (rev, pid) in used: continue
            used.add((rev, pid))
            writer.writerow([rid, pid, rev, fake.random_int(1, 5), fake.sentence(12), '', fake.date_time(), fake.date_time()])
            rid += 1
    return used, rid


def gen_extra_product_reviews_for_test(extra, available, used_existing, start):
    with open('Product_Reviews.csv', 'a') as f:
        writer = get_csv_writer(f)
        rid = start
        for _ in range(extra):
            pid = fake.random_element([p for p in available if (TOKEN_USER_ID, p) not in used_existing])
            used_existing.add((TOKEN_USER_ID, pid))
            writer.writerow([rid, pid, TOKEN_USER_ID, fake.random_int(1, 5), fake.sentence(12), '', fake.date_time(), fake.date_time()])
            rid += 1


def gen_seller_reviews(count):
    used = set()
    with open('Seller_Reviews.csv', 'w') as f:
        writer = get_csv_writer(f)
        sid = 0
        while sid < count:
            rev = fake.random_int(0, num_users)
            sel = fake.random_int(0, num_users)
            if rev == sel or (rev, sel) in used: continue
            used.add((rev, sel))
            writer.writerow([sid, sel, rev, fake.random_int(1, 5), fake.sentence(12), '', fake.date_time(), fake.date_time()])
            sid += 1
    return used, sid


def gen_extra_seller_reviews_for_test(extra, used_existing, start):
    with open('Seller_Reviews.csv', 'a') as f:
        writer = get_csv_writer(f)
        sid = start
        for _ in range(extra):
            # by test user
            sel = fake.random_int(0, num_users)
            if (TOKEN_USER_ID, sel) not in used_existing:
                used_existing.add((TOKEN_USER_ID, sel))
                writer.writerow([sid, sel, TOKEN_USER_ID, fake.random_int(1, 5), fake.sentence(12), '', fake.date_time(), fake.date_time()])
                sid += 1
        for _ in range(extra):
            # for test user
            rev = fake.random_int(0, num_users)
            if (rev, TOKEN_USER_ID) not in used_existing:
                used_existing.add((rev, TOKEN_USER_ID))
                writer.writerow([sid, TOKEN_USER_ID, rev, fake.random_int(1, 5), fake.sentence(12), '', fake.date_time(), fake.date_time()])
                sid += 1

# Generate Categories first
with open('Categories.csv', 'w') as f:
    writer = get_csv_writer(f)
    writer.writerow([1, "Electronics", "Electronic devices and accessories"])
    writer.writerow([2, "Clothing", "Apparel and fashion items"])
    writer.writerow([3, "Home & Kitchen", "Home appliances and kitchenware"])

# Generate the rest of the data
gen_users(num_users)
available_pids = gen_products(num_products, num_users)
gen_inventory(num_products)
gen_purchases(num_purchases, available_pids, num_users)

# Generate 45 orders for user_id 100 (the test user)
gen_user_purchases(100, 45, available_pids)

# Generate 45 orders where user_id 100 is the seller
gen_seller_orders(45, 100, available_pids)
existing_pr, next_pr = gen_product_reviews(NUM_PRODUCT_REVIEWS, available_pids)
gen_extra_product_reviews_for_test(EXTRA_TEST_USER_PRODUCT_REVIEWS, available_pids, existing_pr, next_pr)
existing_sr, next_sr = gen_seller_reviews(NUM_SELLER_REVIEWS)
gen_extra_seller_reviews_for_test(EXTRA_TEST_USER_SELLER_REVIEWS_BY, existing_sr, next_sr)