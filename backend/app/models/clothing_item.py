from ..extensions import db


class ClothingItem(db.Model):
    __tablename__ = "clothing_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    image_url = db.Column(db.String(255), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    subcategory = db.Column(db.String(100), nullable=True)
    colors = db.Column(db.JSON, nullable=False, default=list)
    styles = db.Column(db.JSON, nullable=False, default=list)
    season = db.Column(db.String(50), nullable=False, default="all-season")
    formality = db.Column(db.String(50), nullable=False, default="casual")
    fit = db.Column(db.String(50), nullable=True)
    layer_level = db.Column(db.String(50), nullable=True)
    insulation_rating = db.Column(db.Float, nullable=False, default=0.0)
    waterproof = db.Column(db.Boolean, nullable=False, default=False)
    windproof = db.Column(db.Boolean, nullable=False, default=False)
    material = db.Column(db.String(80), nullable=True)

    user = db.relationship("User", back_populates="clothing_items")
    outfit_items = db.relationship(
        "OutfitItem",
        back_populates="clothing_item",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "image_url": self.image_url,
            "title": self.title,
            "category": self.category,
            "subcategory": self.subcategory,
            "colors": self.colors or [],
            "styles": self.styles or [],
            "season": self.season,
            "formality": self.formality,
            "fit": self.fit,
            "layer_level": self.layer_level,
            "insulation_rating": self.insulation_rating,
            "waterproof": self.waterproof,
            "windproof": self.windproof,
            "material": self.material,
        }
