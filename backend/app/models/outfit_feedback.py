from ..extensions import db


class OutfitFeedback(db.Model):
    __tablename__ = "outfit_feedback"
    __table_args__ = (
        db.UniqueConstraint("outfit_id", "user_id", name="uq_outfit_feedback_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    outfit_id = db.Column(db.Integer, db.ForeignKey("outfits.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    reaction = db.Column(db.String(20), nullable=False)

    outfit = db.relationship("Outfit", back_populates="feedback_entries")
    user = db.relationship("User", back_populates="outfit_feedback")

    def to_dict(self):
        return {
            "id": self.id,
            "outfit_id": self.outfit_id,
            "user_id": self.user_id,
            "reaction": self.reaction,
        }
