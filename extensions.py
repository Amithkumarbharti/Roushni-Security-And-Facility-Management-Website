"""
Shared extension instances. Kept in their own module so both app.py and
models.py can import `db` without a circular import.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
