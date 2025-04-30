from flask_login import UserMixin
from flask import current_app as app
from werkzeug.security import check_password_hash, generate_password_hash
from .. import login
from ..security import SecurityValidation, PasswordSecurity, SQLInjectionPrevention


class User(UserMixin):
    def __init__(self, id, email, firstname, lastname):
        self.id = id
        self.email = email
        self.firstname = firstname
        self.lastname = lastname

    @staticmethod
    def get_by_auth(email, password):
        # Validate and sanitize input
        if not SecurityValidation.validate_pattern(email, 'email'):
            return None
        
        email = SecurityValidation.sanitize_input(email)
        
        # Use safe query execution
        rows = SQLInjectionPrevention.safe_execute_query(
            app.db,
            """
            SELECT password, id, email, firstname, lastname
            FROM Users
            WHERE email = :email
            """,
            {'email': email}
        )
        
        if not rows:  # email not found
            return None
        elif not check_password_hash(rows[0][0], password):
            # incorrect password
            return None
        else:
            return User(*(rows[0][1:]))

    @staticmethod
    def email_exists(email):
        # Validate and sanitize input
        if not SecurityValidation.validate_pattern(email, 'email'):
            return False
            
        email = SecurityValidation.sanitize_input(email)
        
        # Use safe query execution
        rows = SQLInjectionPrevention.safe_execute_query(
            app.db,
            """
            SELECT email
            FROM Users
            WHERE email = :email
            """,
            {'email': email}
        )
        return len(rows) > 0

    @staticmethod
    def register(email, password, firstname, lastname):
        try:
            # Basic validation
            if not all([email, password, firstname, lastname]):
                return None
            
            # Simple password check
            if len(password) < 6:
                raise ValueError("Password must be at least 6 characters long")
            
            # Hash password
            hashed_password = generate_password_hash(password)
            
            # Use safe query execution
            rows = app.db.execute("""
                INSERT INTO Users(email, password, firstname, lastname)
                VALUES(:email, :password, :firstname, :lastname)
                RETURNING id
                """,
                email=email,
                password=hashed_password,
                firstname=firstname,
                lastname=lastname)
            
            id = rows[0][0]
            return User.get(id)
        except Exception as e:
            print(f"Error in user registration: {str(e)}")
            return None

    @staticmethod
    @login.user_loader
    def get(id):
        # Validate id is numeric
        try:
            id = int(id)
        except (TypeError, ValueError):
            return None
            
        # Use safe query execution
        rows = SQLInjectionPrevention.safe_execute_query(
            app.db,
            """
            SELECT id, email, firstname, lastname
            FROM Users
            WHERE id = :id
            """,
            {'id': id}
        )
        return User(*(rows[0])) if rows else None

