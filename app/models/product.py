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
    def get_all_top5(available=True):
        rows = app.db.execute('''
SELECT product_id AS id, name, price, description, image_url, seller_id, category_id
FROM Products  
ORDER BY RANDOM()  
LIMIT 5
''',
                             available=available)
        return [
            Product(
                row[0],  # product_id -> index 0
                row[1],  # name -> index 1
                row[2],  # price -> index 2
                row[3],  # description -> index 3
                get_bing_square_image(row[1]),  # image_url from Bing, using name (index 1)
                row[5],  # seller_id -> index 5
                row[6]   # category_id -> index 6
            )
        for row in rows
        ]
        
    @staticmethod
    def get_filtered_top5(review, min_price, max_price, available=True):
        rows = app.db.execute('''
SELECT product_id AS id, name, price, description, image_url, seller_id, category_id
FROM Products  
WHERE available = :available  
AND price BETWEEN :min_price AND :max_price  
AND avg_review >= :review  
ORDER BY avg_review ASC, RANDOM()  
LIMIT 5;
''',
                             available=available, review=review, 
                             min_price=min_price, max_price=max_price
                             )
        return [Product(*row) for row in rows]
    

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
    