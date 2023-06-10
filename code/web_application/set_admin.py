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
        default="config.RedShiftConfig",
        help="Python import string to the desired Flask config object.",
    )
    parser.add_argument(
        "email",
        type=str,
        help="Email of the account you want to promote",
    )
    args = parser.parse_args()
    app = create_app(config=args.config)

    from flask_app.models import Users
    with app.app_context():
        try:  # for some reason this tries to add the user twice, and fails the second time due to unique email constraint on the db.
            Users.set_admin(args.email, 2)
        except Exception as e:
            logging.error(f"error: {e.__class__.__name__}: {e}")
