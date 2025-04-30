from typing import Union, Any, Optional
import re
from functools import wraps
from flask import request, abort, current_app
import sqlalchemy
from werkzeug.security import generate_password_hash
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityValidation:
    # Regular expressions for validation
    PATTERNS = {
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'name': r'^[a-zA-Z0-9\s\-\']+$',
        'price': r'^\d+(\.\d{1,2})?$',
        'quantity': r'^\d+$'
    }

    # Input length constraints
    LENGTH_LIMITS = {
        'email': 255,
        'name': 255,
        'description': 1000,
        'password': 72,  # bcrypt max length
        'search_query': 255
    }

    @staticmethod
    def sanitize_input(value: str) -> str:
        """Basic input sanitization"""
        if value is None:
            return None
        # Remove any null bytes
        value = value.replace('\x00', '')
        # Convert to string and strip whitespace
        return str(value).strip()

    @staticmethod
    def validate_pattern(value: str, pattern_name: str) -> bool:
        """Validate input against predefined patterns"""
        if value is None:
            return False
        pattern = SecurityValidation.PATTERNS.get(pattern_name)
        if not pattern:
            return False
        return bool(re.match(pattern, str(value)))

    @staticmethod
    def validate_length(value: str, field_name: str) -> bool:
        """Validate input length against predefined limits"""
        if value is None:
            return True
        max_length = SecurityValidation.LENGTH_LIMITS.get(field_name)
        if not max_length:
            return True
        return len(str(value)) <= max_length

    @staticmethod
    def validate_numeric_range(value: Union[int, float], min_val: float, max_val: float) -> bool:
        """Validate numeric input within range"""
        try:
            num_value = float(value)
            return min_val <= num_value <= max_val
        except (TypeError, ValueError):
            return False

class SQLInjectionPrevention:
    @staticmethod
    def parameterize_query(query: str, params: dict) -> tuple:
        """Convert a query with parameters into a safe parameterized query"""
        try:
            # Use SQLAlchemy's text() to create parameterized query
            from sqlalchemy import text
            return text(query), params
        except Exception as e:
            logger.error(f"Error in parameterize_query: {str(e)}")
            raise

    @staticmethod
    def safe_execute_query(db, query: str, params: dict = None) -> Any:
        """Safely execute a database query with parameters"""
        try:
            if params is None:
                params = {}
            
            # Validate and sanitize parameters
            sanitized_params = {
                k: SecurityValidation.sanitize_input(str(v))
                for k, v in params.items()
            }
            
            # Use the db.execute method directly with the sanitized parameters
            # Note: Your DB class expects kwargs to be unpacked
            return db.execute(query, **sanitized_params)
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            raise

def require_api_key(f):
    """Decorator to require API key for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config['API_KEY']:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

class PasswordSecurity:
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Basic password validation - just check if it's not empty and has minimum length
        """
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters long"
        return True, "Password is valid"

    @staticmethod
    def hash_password(password: str) -> str:
        """Securely hash password"""
        return generate_password_hash(password)

class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
        
        # Add security headers
        @app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Updated CSP to allow necessary resources
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'"
            )
            response.headers['Content-Security-Policy'] = csp
            return response
        
        # Log security events
        @app.before_request
        def log_request_info():
            logger.info(f'Request: {request.method} {request.url} from {request.remote_addr}') 