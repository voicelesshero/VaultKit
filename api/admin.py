from flask import Blueprint, jsonify
import re
import models
import config

admin_bp = Blueprint("admin", __name__)


def _mask_db_url(url):
    """Replace the password in a postgres URL with ***."""
    if not url:
        return None
    return re.sub(r"(?<=:)[^:@]+(?=@)", "***", url)


@admin_bp.route("/admin/db-info")
def db_info():
    masked_url = _mask_db_url(config.DATABASE_URL) or "Not set (using SQLite)"

    try:
        conn = models.get_db()
        c = models._cursor(conn)

        c.execute("SELECT COUNT(*) FROM users")
        row = c.fetchone()
        user_count = row[0] if row else "error"

        if config.USE_POSTGRES:
            c.execute("SELECT version()")
            ver_row = c.fetchone()
            db_version = ver_row[0] if ver_row else "unknown"
        else:
            c.execute("SELECT sqlite_version()")
            ver_row = c.fetchone()
            db_version = f"SQLite {ver_row[0]}" if ver_row else "unknown"

        conn.close()
    except Exception as e:
        return jsonify({"error": str(e), "database_url": masked_url}), 500

    return jsonify({
        "database_url": masked_url,
        "engine": "postgresql" if config.USE_POSTGRES else "sqlite",
        "user_count": user_count,
        "db_version": db_version,
    })
