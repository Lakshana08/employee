from functools import wraps
from flask import request, jsonify
import hashlib
from db import employees
from flask import g

def token_required(required_role="HR"):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 1. Get token from Authorization header
            raw_token = request.headers.get("Authorization")
            if not raw_token:
                return jsonify({"error": "Missing token"}), 401

            # Strip "Bearer " if present
            if raw_token.startswith("Bearer "):
                raw_token = raw_token.split(" ", 1)[1]

            # 2. Hash the token
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

            # 3. Find user by token hash
            user = next((u for u in employees.values() if u.get("token_hash") == token_hash), None)
            if not user:
                return jsonify({"error": "Invalid token"}), 403

            # 4. Check role if required
            if required_role and user["role"] != required_role:
                return jsonify({"error": "Access denied"}), 403

            # 5. Attach user info if needed
            g.user = user

            return f(*args, **kwargs)
        return wrapper
    return decorator
