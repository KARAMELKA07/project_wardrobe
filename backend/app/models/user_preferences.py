from ..extensions import db


class UserPreferences(db.Model):
    __tablename__ = "user_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    preferred_styles = db.Column(db.JSON, nullable=False, default=list)
    preferred_colors = db.Column(db.JSON, nullable=False, default=list)
    constraints = db.Column(db.JSON, nullable=False, default=list)
    disliked_items = db.Column(db.JSON, nullable=False, default=list)

    user = db.relationship("User", back_populates="preferences")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "preferred_styles": self.preferred_styles or [],
            "preferred_colors": self.preferred_colors or [],
            "constraints": self.constraints or [],
            "disliked_items": self.disliked_items or [],
        }
