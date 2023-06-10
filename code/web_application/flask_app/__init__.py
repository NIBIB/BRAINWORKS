from flask import Flask, request, redirect, session
from flask_session import Session
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from flask_wtf.csrf import CSRFProtect
import flask_migrate
import neverbounce_sdk
import logging
import os
from flask_gtts import gtts
from datetime import timedelta

# "compare_type" ensures that column type modifications are properly detected
# "render_as_batch" runs all changes in a single block. Also allows more flexibility with SQLite.
migrate = flask_migrate.Migrate(compare_type=True, render_as_batch=True)

# user database
ldb = SQLAlchemy()

# Initialize login manager
login_manager = LoginManager()

# csrf protection
csrf = CSRFProtect()

# Google text to speech (CAPTCHA)
gtts_obj = gtts(temporary=True)


def create_app(config=None):
    """Construct the core flask_session_tutorial."""
    # Must static_folder=None to disable the default /static route from interfering with serving the React files.
    # Yes, this is apparently necessary even though we explicitly set the static folder later because Flask is just like that.
    application = Flask(__name__, instance_relative_config=False, static_folder=None)

    if config:  # if given, use the specified configuration import path
        application.config.from_object(config)
    else:  # default to development environment if not specified
        application.config.from_object("config.DevConfig")

    # configure root logger (this must be placed before any logging is done or it won't work)
    logging.getLogger("werkzeug").level = logging.INFO
    logging.basicConfig(
        filename="./logs/flask.log",
        filemode="w",
        level=application.config["LOG_LEVEL"],
        style="{",
        format="{asctime} {levelname} {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info(f"Using config: ${config}")
    logging.info(f"User database URI: {application.config['SQLALCHEMY_DATABASE_URI']}")

    # now set the static files folder for real this time
    if application.config.get("STATIC_FOLDER"):
        logging.info(f"static folder: {application.config.get('STATIC_FOLDER')}")
        application.static_folder = application.config.get("STATIC_FOLDER")


    # Initialize Server-side session manager
    Session(application)

    # Enable CSRF protection
    csrf.init_app(application)

    with application.app_context():
        # Initialize extensions
        login_manager.init_app(application)
        ldb.init_app(application)
        migrate.init_app(application, ldb)  # initialize migration manager
        application.neverbounce = neverbounce_sdk.client(
            api_key=application.config["NEVERBOUNCE_KEY"], timeout=30
        )

        # Import blueprints
        from .home.home import home
        from .auth.auth import auth
        from .admin.admin import admin
        from .react_forms.react_forms import react_forms

        # Register blueprints
        application.register_blueprint(home)
        application.register_blueprint(auth)
        application.register_blueprint(admin)
        application.register_blueprint(react_forms)

        # Redirect to HTTPS
        @application.before_request
        def before_request():
            if not request.is_secure and not application.config["DEBUG"] and application.config['SESSION_COOKIE_SECURE']:
                url = request.url.replace("http://", "https://", 1)
                return redirect(url, code=301)

        # Now, after all other routes have been registered (above), add a catch-all route to server the React files.
        @application.route("/", defaults={"path": ""})
        @application.route("/<path:path>")
        def catch_all(path):
            if path != "" and os.path.exists(
                application.static_folder + "/" + path
            ):  # serve the react file if it exists
                return application.send_static_file(path)
            else:  # otherwise serve the main page
                return application.send_static_file("index.html")

        # Enable lifetime for session for 20 minutes of inactivity
        @application.before_request
        def before_request():
            session.permanent = True
            application.permanent_session_lifetime = timedelta(hours=2)
            session.modified = True

        # Enable GTTS
        gtts_obj.init_app(application)

        # Logs user accesses
        @application.before_request
        def log_user():
            assets = [".png", ".gif", ".jpg", ".jpeg", ".ico", ".js"]
            if not request.url.endswith(tuple(assets)):
                logging.info(f"User: {current_user.get_id()} URL: {request.url}")

        # Initialize scheduler
        scheduler = APScheduler()
        scheduler.init_app(application)

        # if in redshift environment, use the redshift queries
        if application.config.get("DATA_DATABASE") == "REDSHIFT":
            logging.info("Using RedShift database")
            from .utils.graph.redshift_get_graph import get_autocomplete_files
        else:  # otherwise use the MySQL queries
            logging.info("Using MySQL database")
            from .utils.graph.get_graph import get_autocomplete_files
        get_autocomplete_files(replace=False)  # run once on start if files don't already exist
        @scheduler.task("interval", id="update_autocomplete", days=7)
        def update_autocomplete():
            get_autocomplete_files(replace=True)  # update autocomplete files

        scheduler.start()

        return application
