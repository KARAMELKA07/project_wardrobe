from .analytics import analytics_bp
from .auth import auth_bp
from .items import items_bp
from .outfits import outfits_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(outfits_bp)
    app.register_blueprint(analytics_bp)
