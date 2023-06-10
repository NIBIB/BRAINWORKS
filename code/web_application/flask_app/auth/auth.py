from flask import Blueprint, session, request, jsonify, make_response
from flask import current_app as app
from flask_login import logout_user, current_user
import requests

from ..utils.errors.errors import log_msg
from flask_app.utils.api.api import return_dict_user
from ..utils.captcha import generate_math
from flask_app.models import Users


# Blueprint Configuration
auth = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/auth",
)


@app.login_manager.user_loader
def load_user(ID):
    """User loader function for the LoginManager"""
    if ID is not None:
        try:
            return Users.query.get(ID)  # get user with this ID, if it exists
        except Exception as e:
            log_msg(
                request.url,
                f"Error loading user (ID {ID}): {e.__class__.__name__}: {e}",
            )
            return None
    return None


@app.route("/api/captcha/gtts", methods=["GET"])
def api_captcha_tts():
    """
    Checks session for the math session
    """
    question = session["math_question"]
    try:
        # TODO: use environmental variables, remove audio file once
        res = requests.get(app.config["DOMAIN_NAME"] + "/gtts/en-us/" + question)
        data = res.json()
        data = data.get("mp3")
        return jsonify(data)
    except:
        return ""


@app.route("/api/get_captcha/gtts", methods=["GET"])
def get_captcha_tts():
    """
    Checks session for the math session
    """
    question = session["math_question"]
    try:
        # TODO: use environmental variables, remove audio file once
        res = requests.get(app.config["DOMAIN_NAME"] + "/gtts/en-us/" + question)
        data = res.json()
        data = data.get("mp3")
        return make_response(jsonify(data))
    except:
        return make_response(jsonify("error"))


@app.route("/api/new_captcha", methods=["GET"])
def api_new_captcha():
    """
    Generates new CAPTCHA
    """
    question, answer, text = generate_math()  # create new question
    session["math_answer"] = answer  # set new answer in session
    session["math_question"] = text  # set text question in session
    # audio_link = gtts_obj.say(lang="en", text=text)
    # audio_link = audio_link[1:]
    audio_link = ""

    return jsonify({"img": question, "audio": audio_link})


@app.route("/api/user_session", methods=["GET"])
def user_session():
    """
    User Session

    Tests if user has a previous session (logged in), if so return user's data. This route is fetched on page reload.
    """

    try:
        response = jsonify(return_dict_user(current_user))
        return response
    except:
        # This doesn't matter what it returns, just needs false as isLoggedIn
        return jsonify({"isLoggedIn": False})


@app.route("/api/logout", methods=["GET"])
def api_signout():
    """
    Log out the current user from session
    """
    # Checks if user is already authenticated
    if not current_user.is_authenticated:
        return jsonify(error="Already logged out")

    # Otherwise, try and log the user out
    try:
        logout_user()
    except Exception as e:
        log_msg(request.url, f"Error logging out user: {str(e)}")
        return jsonify(error="Error logging out user")

    if session.get(
        "next"
    ):  # manually remove "next" url from session TODO: submit a pull request to do this natively?
        del session["next"]

    return jsonify(success="Logged out")
