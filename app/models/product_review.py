from flask import current_app as app
from datetime import datetime

class ProductReview:
    def __init__(self, review_id, product_id, reviewer_id, rating, review_text, image_url, created_at, updated_at):
        self.review_id = review_id
        self.product_id = product_id
        self.reviewer_id = reviewer_id
        self.rating = rating
        self.review_text = review_text
        self.image_url = image_url
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def get_by_product(product_id):
        rows = app.db.execute('''
            SELECT review_id, product_id, reviewer_id, rating, review_text, image_url, created_at, updated_at
            FROM Product_Reviews
            WHERE product_id = :product_id
        ''', product_id=product_id)
        return [ProductReview(*row) for row in rows]

    @staticmethod
    def get_by_user(user_id):
        rows = app.db.execute('''
            SELECT review_id, product_id, reviewer_id, rating, review_text, image_url, created_at, updated_at
            FROM Product_Reviews
            WHERE reviewer_id = :user_id
        ''', user_id=user_id)
        return [ProductReview(*row) for row in rows]

    @staticmethod
    def create(product_id, reviewer_id, rating, review_text=None, image_url=None):
        rows = app.db.execute('''
            INSERT INTO Product_Reviews (product_id, reviewer_id, rating, review_text, image_url)
            VALUES (:product_id, :reviewer_id, :rating, :review_text, :image_url)
            RETURNING review_id, product_id, reviewer_id, rating, review_text, image_url, created_at, updated_at
        ''',
        product_id=product_id,
        reviewer_id=reviewer_id,
        rating=rating,
        review_text=review_text,
        image_url=image_url)

        return ProductReview(*rows[0]) if rows else None

    @staticmethod
    def update(review_id, rating=None, review_text=None, image_url=None):
        row = app.db.execute('''
            UPDATE Product_Reviews
            SET rating = COALESCE(:rating, rating),
                review_text = COALESCE(:review_text, review_text),
                image_url = COALESCE(:image_url, image_url),
                updated_at = CURRENT_TIMESTAMP
            WHERE review_id = :review_id
            RETURNING review_id, product_id, reviewer_id, rating, review_text, image_url, created_at, updated_at
        ''',
        review_id=review_id,
        rating=rating,
        review_text=review_text,
        image_url=image_url)

        return ProductReview(*row[0]) if row else None

    @staticmethod
    def delete(review_id):
        app.db.execute('''
            DELETE FROM Product_Reviews
            WHERE review_id = :review_id
        ''', review_id=review_id)
