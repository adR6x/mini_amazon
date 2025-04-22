from flask import current_app as app
import requests
from bs4 import BeautifulSoup

# Helper to fetch a 200x200 image URL from Bing Images
def get_bing_square_image(query):
    search_url = f"https://www.bing.com/images/search?q={query}&qft=+filterui:imagesize-custom_200_200&form=HDRSC2"
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


class Product:
    def __init__(
        self,
        id,
        name,
        price,
        description=None,
        image_url=None,
        seller_id=None,
        category_id=None,
        number_of_reviews=0,
        average_rating=0.0,
    ):
        self.id = id
        self.name = name
        self.price = price
        self.description = description
        self.image_url = image_url
        self.seller_id = seller_id
        self.category_id = category_id
        self.number_of_reviews = number_of_reviews
        self.average_rating = float(average_rating)

    @staticmethod
    def get(id):
        rows = app.db.execute('''
SELECT
  p.product_id   AS id,
  p.name,
  p.price,
  p.description,
  p.image_url,
  p.seller_id,
  p.category_id,
  COUNT(pr.review_id)      AS number_of_reviews,
  COALESCE(AVG(pr.rating), 0) AS average_rating
FROM Products p
LEFT JOIN Product_Reviews pr
  ON pr.product_id = p.product_id
WHERE p.product_id = :id
GROUP BY
  p.product_id, p.name, p.price,
  p.description, p.image_url,
  p.seller_id, p.category_id
''', id=id)
        return Product(*rows[0]) if rows else None

    @staticmethod
    def get_all():
        rows = app.db.execute('''
SELECT
  p.product_id   AS id,
  p.name,
  p.price,
  p.description,
  p.image_url,
  p.seller_id,
  p.category_id,
  COUNT(pr.review_id)      AS number_of_reviews,
  COALESCE(AVG(pr.rating), 0) AS average_rating
FROM Products p
LEFT JOIN Product_Reviews pr
  ON pr.product_id = p.product_id
GROUP BY
  p.product_id, p.name, p.price,
  p.description, p.image_url,
  p.seller_id, p.category_id
''')
        return [Product(*row) for row in rows]

    @staticmethod
    def get_all_rnd5():
        rows = app.db.execute('''
SELECT
  p.product_id   AS id,
  p.name,
  p.price,
  p.description,
  p.image_url,
  p.seller_id,
  p.category_id,
  COUNT(pr.review_id)      AS number_of_reviews,
  COALESCE(AVG(pr.rating), 0) AS average_rating
FROM Products p
LEFT JOIN Product_Reviews pr
  ON pr.product_id = p.product_id
GROUP BY
  p.product_id, p.name, p.price,
  p.description, p.image_url,
  p.seller_id, p.category_id
ORDER BY RANDOM()
LIMIT 5
''')
        return [Product(*row) for row in rows]

    @staticmethod
    def get_filtered_top_exp(most_exp):
        rows = app.db.execute('''
SELECT
  p.product_id   AS id,
  p.name,
  p.price,
  p.description,
  p.image_url,
  p.seller_id,
  p.category_id,
  COUNT(pr.review_id)      AS number_of_reviews,
  COALESCE(AVG(pr.rating), 0) AS average_rating
FROM Products p
LEFT JOIN Product_Reviews pr
  ON pr.product_id = p.product_id
GROUP BY
  p.product_id, p.name, p.price,
  p.description, p.image_url,
  p.seller_id, p.category_id
ORDER BY p.price DESC
LIMIT :most_exp
''', most_exp=most_exp)
        return [Product(*row) for row in rows]

    @staticmethod
    def get_filtered_all(review, min_price, max_price, most_exp):
        rows = app.db.execute('''
SELECT
  p.product_id   AS id,
  p.name,
  p.price,
  p.description,
  p.image_url,
  p.seller_id,
  p.category_id,
  COUNT(pr.review_id)      AS number_of_reviews,
  COALESCE(AVG(pr.rating), 0) AS average_rating
FROM Products p
LEFT JOIN Product_Reviews pr
  ON pr.product_id = p.product_id
WHERE p.price BETWEEN :min_price AND :max_price
GROUP BY
  p.product_id, p.name, p.price,
  p.description, p.image_url,
  p.seller_id, p.category_id
HAVING AVG(pr.rating) >= :review
ORDER BY p.price DESC
LIMIT :most_exp
''',
            review=review,
            min_price=min_price,
            max_price=max_price,
            most_exp=most_exp
        )
        return [Product(*row) for row in rows]

    @staticmethod
    def get_by_cat(category_id):
        rows = app.db.execute('''
SELECT
  p.product_id   AS id,
  p.name,
  p.price,
  p.description,
  p.image_url,
  p.seller_id,
  p.category_id,
  COUNT(pr.review_id)      AS number_of_reviews,
  COALESCE(AVG(pr.rating), 0) AS average_rating
FROM Products p
LEFT JOIN Product_Reviews pr
  ON pr.product_id = p.product_id
WHERE p.category_id = :category_id
GROUP BY
  p.product_id, p.name, p.price,
  p.description, p.image_url,
  p.seller_id, p.category_id
LIMIT 5
''', category_id=category_id)
        return [Product(*row) for row in rows]

    @staticmethod
    def get_by_search(query):
        rows = app.db.execute('''
CREATE EXTENSION IF NOT EXISTS pg_trgm;
SET pg_trgm.similarity_threshold = 0.2;
SELECT
  p.product_id       AS id,
  p.name,
  p.price,
  p.description,
  p.image_url,
  p.seller_id,
  p.category_id,
  pr_agg.number_of_reviews,
  pr_agg.average_rating,
  GREATEST(
    similarity(p.name::TEXT,    CAST(:query AS TEXT)),
    similarity(p.description,   CAST(:query AS TEXT)),
    similarity(u.firstname,     CAST(:query AS TEXT)),
    similarity(u.lastname,      CAST(:query AS TEXT)),
    similarity(u.address,       CAST(:query AS TEXT)),
    similarity(c.name,          CAST(:query AS TEXT)),
    similarity(c.description,   CAST(:query AS TEXT))
  ) AS rank
FROM Products p
LEFT JOIN users u
  ON p.seller_id = u.id
LEFT JOIN categories c
  ON p.category_id = c.category_id
LEFT JOIN LATERAL (
  SELECT
    COUNT(*)               AS number_of_reviews,
    COALESCE(AVG(rating),0) AS average_rating
  FROM Product_Reviews pr
  WHERE pr.product_id = p.product_id
) pr_agg ON true
WHERE
  p.name        % :query OR
  p.description % :query OR
  u.firstname   % :query OR
  u.lastname    % :query OR
  u.address     % :query OR
  c.name        % :query OR
  c.description % :query
ORDER BY rank DESC
LIMIT 5;
''', query=str(query))
        return [Product(*row) for row in rows]


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
