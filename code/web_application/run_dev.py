import argparse
from flask_app import create_app
from flask_migrate import upgrade
import logging

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process args")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.DevConfig",
        help="Python import string to the desired Flask config object.",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default="5000",
        help="Port at which to locally host the site.",
    )
    args = parser.parse_args()
    app = create_app(config=args.config)

    from flask_app.models import Users
    with app.app_context():
        upgrade()

    app.run(host="0.0.0.0", port=args.port)
