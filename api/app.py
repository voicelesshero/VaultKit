from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from datetime import timedelta
import config
import models
from auth import auth_bp
from sync import sync_bp
from account import account_bp

app = Flask(__name__)

# JWT configuration
app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=config.JWT_ACCESS_TOKEN_EXPIRES_HOURS)

jwt = JWTManager(app)

# Register blueprints — each one brings its own group of routes
app.register_blueprint(auth_bp)
app.register_blueprint(sync_bp)
app.register_blueprint(account_bp)

# Create database tables on startup if they don't exist yet
with app.app_context():
    models.init_db()


@app.route("/")
def index():
    return jsonify({"message": "VaultKit API is running", "version": "2.0"})


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
