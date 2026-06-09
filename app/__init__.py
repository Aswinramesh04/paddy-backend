"""
Import all models here so SQLAlchemy's metadata knows about them.
Alembic autogenerate also needs this import.
"""
from app.models.disease import Disease, PreventionTip, Recommendation
from app.models.prediction import Prediction
from app.models.shop import Shop
from app.models.user import User
from app.models.password_reset import PasswordReset

__all__ = [
    "User",
    "PasswordReset",
    "Disease",
    "Recommendation",
    "PreventionTip",
    "Prediction",
    "Shop",
]