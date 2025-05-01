from flask import current_app as app

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
''')
        return [Product(*row) for row in rows]

    @staticmethod
    def get_filtered_all(review=None, min_price=None, max_price=None, most_exp=None, category_id=None):
        base_query = '''
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
        WHERE 1=1
        '''
        params = {}
        
        if min_price is not None:
            base_query += " AND p.price >= :min_price"
            params['min_price'] = min_price
        if max_price is not None:
            base_query += " AND p.price <= :max_price"
            params['max_price'] = max_price
        if category_id:
            base_query += " AND p.category_id = :category_id"
            params['category_id'] = category_id

        base_query += '''
        GROUP BY
          p.product_id, p.name, p.price,
          p.description, p.image_url,
          p.seller_id, p.category_id
        '''

        if review:
            base_query += " HAVING AVG(pr.rating) >= :review"
            params['review'] = review

        base_query += " ORDER BY p.price DESC"

        if most_exp:
            base_query += " LIMIT :most_exp"
            params['most_exp'] = most_exp

        rows = app.db.execute(base_query, **params)
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
''', category_id=category_id)
        return [Product(*row) for row in rows]

    @staticmethod
    def get_by_search(query):
      rows = app.db.execute(
          '''
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
              COUNT(*)                AS number_of_reviews,
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
          lIMIT 20  
          ''',
          query=str(query)
      )

      products = []
      for row in rows:
          # row[0]–row[8] map to Product fields; row[9] is rank, so we ignore it
          product = Product(
              id=row[0],
              name=row[1],
              price=row[2],
              description=row[3],
              image_url=row[4],
              seller_id=row[5],
              category_id=row[6],
              number_of_reviews=row[7],
              average_rating=row[8]
          )
          products.append(product)

      return products

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
