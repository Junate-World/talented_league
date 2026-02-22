"""
League Site - Production Flask Application Factory
Football league management system similar to English Premier League.
"""

from flask import Flask
from flask_migrate import Migrate

from app.config import config
from app.extensions import (
    db,
    login_manager,
    csrf,
    bcrypt,
)


def create_app(config_name: str = "development") -> Flask:
    """
    Application factory pattern for creating Flask app instances.
    
    Args:
        config_name: Configuration environment (development, production, testing)
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    
    # Initialize Cloudinary if in production
    if app.config.get("USE_CLOUDINARY"):
        import cloudinary
        cloudinary.config(
            cloud_name=app.config.get("CLOUDINARY_CLOUD_NAME"),
            api_key=app.config.get("CLOUDINARY_API_KEY"),
            api_secret=app.config.get("CLOUDINARY_API_SECRET"),
        )
    
    # Configure login manager
    from app.models import User
    from flask_login import set_login_view

    with app.app_context():
        set_login_view("auth.login")
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_commands(app)
    
    # Serve uploaded files
    from flask import send_from_directory
    from app.config import UPLOAD_FOLDER, TEAM_LOGOS_FOLDER, PLAYER_PHOTOS_FOLDER, GALLERY_FOLDER

    @app.route("/uploads/team_logos/<path:filename>")
    def team_logo(filename):
        return send_from_directory(TEAM_LOGOS_FOLDER, filename)

    @app.route("/uploads/player_photos/<path:filename>")
    def player_photo(filename):
        return send_from_directory(PLAYER_PHOTOS_FOLDER, filename)

    @app.route("/uploads/gallery/<path:filename>")
    def gallery_image(filename):
        return send_from_directory(GALLERY_FOLDER, filename)

    # Template filter: resolve image URL (local filename or Cloudinary URL)
    from flask import url_for

    @app.template_filter("asset_url")
    def asset_url_filter(identifier, asset_type="team"):
        if not identifier:
            return None
        if identifier.startswith(("http://", "https://")):
            return identifier
        return url_for(
            "team_logo" if asset_type == "team" else "player_photo",
            filename=identifier,
        )

    return app


def register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.league import league_bp
    from app.blueprints.teams import teams_bp
    from app.blueprints.players import players_bp
    from app.blueprints.matches import matches_bp
    from app.blueprints.gallery import gallery_bp
    from app.blueprints.fan import fan_bp
    from app.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(league_bp, url_prefix="/league")
    app.register_blueprint(teams_bp, url_prefix="/teams")
    app.register_blueprint(players_bp, url_prefix="/players")
    app.register_blueprint(matches_bp, url_prefix="/matches")
    app.register_blueprint(gallery_bp, url_prefix="/gallery")
    app.register_blueprint(fan_bp, url_prefix="/fan")
    app.register_blueprint(api_bp, url_prefix="/api")
    
    # Home / landing page
    @app.route("/")
    def index():
        from flask import render_template
        return render_template("home.html")

    @app.route("/about")
    def about():
        from flask import render_template
        return render_template("about.html")


def register_error_handlers(app: Flask) -> None:
    """Register custom error page handlers."""
    from flask import render_template
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500


def register_commands(app: Flask) -> None:
    """Register Flask CLI commands."""
    @app.cli.command("init-db")
    def init_db():
        """Initialize the database."""
        db.create_all()
        print("Database initialized.")
    
    @app.cli.command("create-admin")
    def create_admin():
        """Create an admin user (run in Flask shell or add proper implementation)."""
        from app.models import User, Role
        from getpass import getpass
        
        email = input("Admin email: ")
        username = input("Admin username: ")
        password = getpass("Admin password: ")
        
        admin_role = Role.query.filter_by(name="Admin").first()
        if not admin_role:
            admin_role = Role()
            admin_role.name = "Admin"
            db.session.add(admin_role)
            db.session.commit()

        user = User()
        user.email = email
        user.username = username
        user.role_id = admin_role.id
        user.password = password
        db.session.add(user)
        db.session.commit()
        print(f"Admin user {username} created successfully.")
