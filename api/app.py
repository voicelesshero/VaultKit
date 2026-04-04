from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import timedelta
import config
import models
from auth import auth_bp, limiter
from sync import sync_bp
from account import account_bp

app = Flask(__name__)

# Trust one layer of reverse proxy headers (X-Forwarded-For etc).
# Required for Railway/Render so rate limiting uses the real client IP,
# not the proxy's IP.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# JWT configuration
app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=config.JWT_ACCESS_TOKEN_EXPIRES_HOURS)

jwt = JWTManager(app)

# Rate limiter — backed by memory (fine for a single instance).
# Swap to Redis via RATELIMIT_STORAGE_URI env var when scaling.
limiter.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(sync_bp)
app.register_blueprint(account_bp)

# Create database tables on startup
with app.app_context():
    models.init_db()


# ---------------------------- SECURITY HEADERS ------------------------------- #

@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


# ---------------------------- ERROR HANDLERS ------------------------------- #
# Return clean JSON errors instead of HTML pages or stack traces.

@app.errorhandler(400)
def bad_request(_e):
    return jsonify({"error": "Bad request."}), 400

@app.errorhandler(401)
def unauthorized(_e):
    return jsonify({"error": "Unauthorized."}), 401

@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "Not found."}), 404

@app.errorhandler(405)
def method_not_allowed(_e):
    return jsonify({"error": "Method not allowed."}), 405

@app.errorhandler(413)
def too_large(_e):
    return jsonify({"error": "Vault file too large."}), 413

@app.errorhandler(429)
def rate_limited(_e):
    return jsonify({"error": "Too many requests. Please wait and try again."}), 429

@app.errorhandler(500)
def internal_error(e):
    # Log the real error server-side but never send it to the client.
    app.logger.error(f"Internal error: {e}")
    return jsonify({"error": "An internal error occurred."}), 500


# ---------------------------- HEALTH CHECK ------------------------------- #

@app.route("/")
def index():
    return jsonify({"message": "VaultKit API is running", "version": "2.0"})


if __name__ == "__main__":
    debug = not config.IS_PRODUCTION
    app.run(debug=debug, use_reloader=False)
