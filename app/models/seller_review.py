from flask import current_app as app
from datetime import datetime

from flask import current_app as app
from sqlalchemy.exc import IntegrityError

class SellerReview:
    def __init__(self, seller_review_id, seller_id, reviewer_id, rating, review_text, image_url, created_at, updated_at, seller_name=None):
        self.seller_review_id = seller_review_id
        self.seller_id = seller_id
        self.reviewer_id = reviewer_id
        self.rating = rating
        self.review_text = review_text
        self.image_url = image_url
        self.created_at = created_at
        self.updated_at = updated_at
        self.seller_name = seller_name

    @staticmethod
    def get_by_seller(seller_id):
        rows = app.db.execute('''
            SELECT
                sr.seller_review_id,
                sr.seller_id,
                sr.reviewer_id,
                sr.rating,
                sr.review_text,
                sr.image_url,
                sr.created_at,
                sr.updated_at,
                u.firstname || ' ' || u.lastname AS seller_name
            FROM Seller_Reviews sr
            JOIN Users u ON sr.seller_id = u.id
            WHERE sr.seller_id = :seller_id
            ORDER BY sr.created_at DESC
        ''',
        seller_id=seller_id)
        return [SellerReview(*row) for row in rows]

    @staticmethod
    def get_by_user(user_id):
        rows = app.db.execute('''
            SELECT
                sr.seller_review_id,
                sr.seller_id,
                sr.reviewer_id,
                sr.rating,
                sr.review_text,
                sr.image_url,
                sr.created_at,
                sr.updated_at,
                u.firstname || ' ' || u.lastname AS seller_name
            FROM Seller_Reviews sr
            JOIN Users u ON sr.seller_id = u.id
            WHERE sr.reviewer_id = :user_id
            ORDER BY sr.created_at DESC
        ''',
        user_id=user_id)
        return [SellerReview(*row) for row in rows]


    @staticmethod
    def _sync_review_seq():
        # adjust sequence name if yours is different
        app.db.execute("""
            SELECT setval(
                pg_get_serial_sequence('Seller_Reviews','seller_review_id'),
                COALESCE(MAX(seller_review_id), 0)
            ) FROM Seller_Reviews
        """)

    @staticmethod
    def create(seller_id, reviewer_id, rating, review_text=None, image_url=None):
        insert_sql = """
            INSERT INTO Seller_Reviews
              (seller_id, reviewer_id, rating, review_text, image_url)
            VALUES
              (:seller_id, :reviewer_id, :rating, :review_text, :image_url)
            RETURNING
              seller_review_id, seller_id, reviewer_id,
              rating, review_text, image_url, created_at, updated_at
        """
        params = {
            "seller_id":   seller_id,
            "reviewer_id": reviewer_id,
            "rating":      rating,
            "review_text": review_text,
            "image_url":   image_url
        }

        # 1) bump the sequence to avoid conflicts
        SellerReview._sync_review_seq()

        try:
            rows = app.db.execute(insert_sql, **params)
        except IntegrityError:
            # 2) if it still collides, sync again and retry once
            SellerReview._sync_review_seq()
            rows = app.db.execute(insert_sql, **params)

        return SellerReview(*rows[0]) if rows else None

    @staticmethod
    def update(seller_review_id, rating=None, review_text=None, image_url=None):
        row = app.db.execute('''
            UPDATE Seller_Reviews
            SET rating = COALESCE(:rating, rating),
                review_text = COALESCE(:review_text, review_text),
                image_url = COALESCE(:image_url, image_url),
                updated_at = CURRENT_TIMESTAMP
            WHERE seller_review_id = :seller_review_id
            RETURNING seller_review_id, seller_id, reviewer_id, rating, review_text, image_url, created_at, updated_at
        ''',
        seller_review_id=seller_review_id,
        rating=rating,
        review_text=review_text,
        image_url=image_url)

        return SellerReview(*row[0]) if row else None

    @staticmethod
    def delete(seller_review_id):
        app.db.execute('''
            DELETE FROM Seller_Reviews
            WHERE seller_review_id = :seller_review_id
        ''', seller_review_id=seller_review_id)

    @staticmethod
    def get_by_id(seller_review_id):
        rows = app.db.execute('''
            SELECT sr.seller_review_id, sr.seller_id, sr.reviewer_id, sr.rating,
                   sr.review_text, sr.image_url, sr.created_at, sr.updated_at,
                   u.firstname || ' ' || u.lastname AS seller_name
            FROM Seller_Reviews sr
            JOIN Users u ON sr.seller_id = u.id
            WHERE sr.seller_review_id = :seller_review_id
        ''', seller_review_id=seller_review_id)
        return SellerReview(*rows[0]) if rows else None

