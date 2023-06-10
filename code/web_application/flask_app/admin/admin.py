from flask import (
    Blueprint,
    abort,
    jsonify,
)
from flask import current_app as app
from flask_login import login_required, current_user
from functools import wraps

from .utils.users import user_charts
from .utils.searches import searches_charts

# TODO: Move edit user form to react_forms

# Blueprint Configuration
admin = Blueprint(
    "admin",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/admin",
)


def admin_required(level):
    """Decorator to restrict access to certain admin levels"""

    def decorator(route):
        @wraps(route)  # keep name of route
        def wrapped(*args, **kwargs):
            assert (
                level > 0
            ), "Should restrict admin routes to admin level 1 or above. Level 0 is a regular user."
            if current_user.admin and current_user.admin >= level:
                return route(*args, **kwargs)
            abort(404)

        return wrapped

    return decorator


@app.route("/api/users_stats", methods=["GET"])
@login_required
@admin_required(1)
def api_users_stats():
    """
    User stats

    Gives statistics for user population and search results
    """
    stats = {}
    stats.update(user_charts())
    stats.update(searches_charts())
    print(stats.keys())
    return jsonify(stats)
