from ..mail.mail import send_mail
from flask_login import current_user
from flask import (
    session, current_app as app
)
from ..api.api import return_dict_user
import logging
import traceback

"""
Error logging utils to see user errors during production

TEMP: Sends to error logging email in order to see errors easily

TODO: Add new logging table
"""


def log_msg(req_url, error_msg, e=None):
    """
    req_url: URL of the request made at the time of the error
    error_msg: error message
    e: Exception object or string, if provided
    """

    logging.error(error_msg)
    if e is not None:  # if an exception object provided
        logging.error(f"{error_msg} - {traceback.format_exc()}")

    if app.config.get("DEBUG"):  # don't send email in debug mode
        return

    divider = f"\n---------------------------\n"

    if current_user.is_authenticated:
        error_msg += f" logged by {current_user.name} (ID: {current_user.id})"
    else:
        error_msg += f" logged by unknown"

    # Title
    error_body = f"Error:\n\n{error_msg}\n"
    error_body += divider
    # Add request URL
    error_body += f"\nRequest URL:\n\n{req_url}\n"
    error_body += divider
    # Print current session
    error_body += f"\nCurrent session:\n"
    if not session:
        error_body += "Session could not be found."
    else:
        for k, v in session.items():
            error_body += f"\n{k} = {v}\n"
    error_body += divider
    # Print current user if they exist
    if current_user.is_authenticated:
        error_body += f"\nCurrent user:\n"
        for k, v in return_dict_user(current_user).items():
            error_body += f"\n{k} = {v}\n"
        error_body += divider

    if app.config['EMAIL']:
        err = send_mail(
            subject=f"{error_msg}",
            recipient=[app.config['EMAIL_ADDRESS']],
            body_text=f"{error_body}",
        )
        if err:
            logging.error(f"Error sending logging email. {e.__class__.__name__}: {e}")