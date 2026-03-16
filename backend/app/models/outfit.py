from ..extensions import db


class Outfit(db.Model):
    __tablename__ = "outfits"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    event_type = db.Column(db.String(80), nullable=False)
    weather_context = db.Column(db.JSON, nullable=True, default=dict)
    score = db.Column(db.Float, nullable=False, default=0.0)
    explanation = db.Column(db.Text, nullable=True)

    user = db.relationship("User", back_populates="outfits")
    items = db.relationship(
        "OutfitItem",
        back_populates="outfit",
        cascade="all, delete-orphan",
    )
    feedback_entries = db.relationship(
        "OutfitFeedback",
        back_populates="outfit",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "event_type": self.event_type,
            "weather_context": self.weather_context or {},
            "score": round(self.score or 0.0, 4),
            "explanation": self.explanation,
            "items": [outfit_item.to_dict() for outfit_item in self.items],
        }


class OutfitItem(db.Model):
    __tablename__ = "outfit_items"

    id = db.Column(db.Integer, primary_key=True)
    outfit_id = db.Column(db.Integer, db.ForeignKey("outfits.id"), nullable=False, index=True)
    clothing_item_id = db.Column(
        db.Integer,
        db.ForeignKey("clothing_items.id"),
        nullable=False,
        index=True,
    )
    role = db.Column(db.String(50), nullable=False)

    outfit = db.relationship("Outfit", back_populates="items")
    clothing_item = db.relationship("ClothingItem", back_populates="outfit_items")

    def to_dict(self):
        return {
            "id": self.id,
            "outfit_id": self.outfit_id,
            "clothing_item_id": self.clothing_item_id,
            "role": self.role,
            "clothing_item": self.clothing_item.to_dict() if self.clothing_item else None,
        }
