from flask import current_app as app
import requests
from bs4 import BeautifulSoup

def get_bing_square_image(query):
    search_url = f"https://www.bing.com/images/search?q={query}&qft=+filterui:imagesize-custom_200_200&form=HDRSC2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        return "Failed to fetch results"

    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.select("img.mimg")

    if img_tags:
        return img_tags[0]["src"]
    return "No image found"

class Product:
    def __init__(self, id, name, price, description=None, image_url=None, seller_id=None, category_id=None):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.description = description
        self.image_url = image_url
        self.seller_id = seller_id
        self.category_id = category_id

    @staticmethod
    def get(id):
        rows = app.db.execute('''
            SELECT product_id AS id, name, price, description, image_url, seller_id, category_id
            FROM Products
            WHERE product_id = :id
        ''', id=id)
        return Product(*rows[0]) if rows else None

    @staticmethod
    def get_all():
        rows = app.db.execute('''
            SELECT product_id AS id, name, price, description, image_url, seller_id, category_id
            FROM Products
        ''')
        return [Product(*row) for row in rows]

    @staticmethod
    def get_all_rnd5():
        rows = app.db.execute('''
SELECT product_id AS id, name, price, description, image_url, seller_id, category_id
FROM Products  
ORDER BY RANDOM()  
LIMIT 5
''',
        )
        return [
            Product(
                id=row[0],  # product_id -> index 0
                name=row[1],  # name -> index 1
                price=row[2],  # price -> index 2
                description=row[3],  # description -> index 3
                image_url=row[4],
                # image_url=get_bing_square_image(row[1]),  # image_url from Bing, using name (index 1)
                seller_id=row[5],  # seller_id -> index 5
                category_id=row[6]   # category_id -> index 6
            )
        for row in rows
        ]
        
    @staticmethod
    def get_filtered_top_exp(most_exp):
        rows = app.db.execute('''
SELECT product_id AS id, name, price, description, image_url, seller_id, category_id
FROM Products
ORDER BY price DESC  
LIMIT :most_exp;
''',
                            most_exp=most_exp
                             )
        return [Product(*row) for row in rows]
        
    @staticmethod
    def get_filtered_all(review, min_price, max_price, most_exp):
        rows = app.db.execute('''
SELECT p.product_id, p.name, p.price, p.description, p.image_url, p.seller_id, p.category_id
FROM products p LEFT JOIN product_reviews pr ON p.product_id = pr.product_id
WHERE price BETWEEN :min_price AND :max_price 
GROUP BY p.product_id, p.name, p.price, p.description, p.image_url
HAVING AVG(pr.rating) >= :review
ORDER BY p.price DESC
LIMIT :most_exp
''',
                            review=review,
                            min_price=min_price, max_price=max_price,
                            most_exp=most_exp
                            )
        return [Product(*row) for row in rows]

    @staticmethod
    def get_by_cat(category_id):
        rows = app.db.execute('''
SELECT product_id AS id, name, price, description, image_url, seller_id, category_id
FROM Products
WHERE category_id = :category_id
LIMIT 5;
''',
                            category_id=category_id
                             )
        return [
            Product(
                id=row[0],  # product_id -> index 0
                name=row[1],  # name -> index 1
                price=row[2],  # price -> index 2
                description=row[3],  # description -> index 3
                image_url=row[4],
                # image_url=get_bing_square_image(row[1]),  # image_url from Bing, using name (index 1)
                seller_id=row[5],  # seller_id -> index 5
                category_id=row[6]   # category_id -> index 6
            )
        for row in rows
        ]
        
    @staticmethod
    def get_by_search(query):
        rows = app.db.execute('''
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
        SET pg_trgm.similarity_threshold = 0.2;
        SELECT 
        p.product_id AS id,
        p.name,
        p.price,
        p.description,
        p.image_url,
        p.seller_id,
        p.category_id,
        GREATEST(
            similarity(p.name::TEXT, CAST(:query AS TEXT)),
            similarity(p.description::TEXT, CAST(:query AS TEXT)),
            similarity(u.firstname::TEXT, CAST(:query AS TEXT)),
            similarity(u.lastname::TEXT, CAST(:query AS TEXT)),
            similarity(u.address::TEXT, CAST(:query AS TEXT)),
            similarity(c.name::TEXT, CAST(:query AS TEXT)),
            similarity(c.description::TEXT, CAST(:query AS TEXT))
        ) AS rank
        FROM Products p
        LEFT JOIN users u ON p.seller_id = u.id
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE
        p.name % :query OR
        p.description % :query OR
        u.firstname % :query OR
        u.lastname % :query OR
        u.address % :query OR
        c.name % :query OR
        c.description % :query
        ORDER BY rank DESC
        LIMIT 5;
        ''', query=str(query))
        return [
            Product(
                id=row[0],  # product_id -> index 0
                name=row[1],  # name -> index 1
                price=row[2],  # price -> index 2
                description=row[3],  # description -> index 3
                image_url=row[4],
                # image_url=get_bing_square_image(row[1]),  # image_url from Bing, using name (index 1)
                seller_id=row[5],  # seller_id -> index 5
                category_id=row[6]   # category_id -> index 6
            )
        for row in rows
        ]        


class Category:
    def __init__(self, id, name, description=None):
        self.id = id
        self.name = name
        self.description = description
        
    @staticmethod
    def get_unique():
        rows = app.db.execute('''
SELECT category_id, name, description
FROM categories
ORDER BY name ASC
        ''')
        return [Category(*row) for row in rows]
    