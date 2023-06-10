# application.py

"""Application entry point."""
from flask_app import create_app
from flask_app.models import Users, UserLog
from flask_app.utils.errors.errors import log_msg
import os

if os.environ.get("REDSHIFT"):  # the redshift backend environment
    config = "config.RedShiftConfig"
else:  # this is production
    config = "config.ProdConfig"

application = None
try:
    application = create_app(config)
except:
    # Log message if application fails to start
    log_msg("Starting application", "Failed to started")

with application.app_context():
    from flask_migrate import upgrade

    # upgrade the user database if necessary
    upgrade()

if __name__ == "__main__":
    application.run(host="0.0.0.0", port="5000")
