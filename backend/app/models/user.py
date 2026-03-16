from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=True)

    preferences = db.relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    clothing_items = db.relationship(
        "ClothingItem",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    outfits = db.relationship(
        "Outfit",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    outfit_feedback = db.relationship(
        "OutfitFeedback",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_preferences=True):
        payload = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "city": self.city,
        }
        if include_preferences:
            payload["preferences"] = (
                self.preferences.to_dict() if self.preferences else None
            )
        return payload
