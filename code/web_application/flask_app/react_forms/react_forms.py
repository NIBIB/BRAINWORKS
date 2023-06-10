from flask import Blueprint, request, jsonify, session
from flask_wtf.csrf import generate_csrf
from flask import current_app as app
from flask_login import current_user

from flask_app.react_forms.utils.forms import (
    ReactForgotPasswordForm,
    ReactLoginForm,
    ReactPaperCitationsForm,
    ReactPaperTriplesForm,
    ReactRequestVerificationEmailForm,
    ReactResetPasswordForm,
    ReactSignUpForm,
    ReactTopicCoOccurencesForm,
    ReactTriplesForm,
    ReactVerifyEmailForm,
    ReactProfileEditPassword,
    ReactProfileEditEmail,
    ReactProfileEditDetails,
    ReactUserSearchForm,
    ReactManagerUserForm,
)
from ..home.home import validate_csrf_post
from ..utils.errors.errors import log_msg
from flask_app.utils.api.api import return_dict_user

react_forms = Blueprint(
    "react_forms",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/react_forms",
)


@app.route("/api/get_auth_status", methods=["GET"])
def get_auth_status():
    """
    Give CSRF token to frontend if it exists, otherwise generates it
    A new CSRF token is created only once per session
    """
    try:
        return jsonify(success=current_user.is_authenticated)
    except:
        log_msg(request.url, f"Couldn't get logged in status")
        return jsonify(error="Couldn't generate CSRF token")


@app.route("/api/get_csrf_token", methods=["GET"])
def get_csrf_token():
    """
    Give CSRF token to frontend if it exists, otherwise generates it
    A new CSRF token is created only once per session
    """
    try:
        csrf_token = session.get("csrf_token")
        if csrf_token == None:
            csrf_token = generate_csrf()
        session["csrf_token"] = csrf_token
        return jsonify(success=csrf_token)
    except:
        log_msg(request.url, f"Couldn't generate CSRF token")
        return jsonify(error="Couldn't generate CSRF token")


@app.route("/api/build_form/<string:form_key>", methods=["GET", "POST"])
@validate_csrf_post
def api_build_send_form(form_key):
    """
    Build / Send Form
    * Form objects are created given form key
    """
    # Form dictionary, holding all associated form objects
    # loop through all forms, inspect classes, check to see what classes, inspect library
    form_dict = {
        # Sign in / up
        "sign_in_form": ReactLoginForm(),
        "sign_up_form": ReactSignUpForm(),
        # Forgot and reset password
        "forgot_password_form": ReactForgotPasswordForm(),
        "reset_password_form": ReactResetPasswordForm(),
        # Request and verify email
        "request_email_verification_form": ReactRequestVerificationEmailForm(),
        "verify_email_form": ReactVerifyEmailForm(),
        # Profile details
        "profile_edit_password_form": ReactProfileEditPassword(),
        "profile_edit_email_form": ReactProfileEditEmail(),
        "profile_edit_details_form": ReactProfileEditDetails(),
        # Admin forms
        "search_user_form": ReactUserSearchForm(),
        "manager_user_form": ReactManagerUserForm(),
        # Tool forms
        "tool_paper_triples_form": ReactPaperTriplesForm(),
        "tool_paper_citations_form": ReactPaperCitationsForm(),
        "tool_topic_co_occurrences_form": ReactTopicCoOccurencesForm(),
        "tool_triples_form": ReactTriplesForm(),
    }
    form = form_dict[form_key]

    # Check if form exists with given key
    if not form:
        log_msg(request.url, "Could not create form, as the form key not found.")
        return jsonify(error="Could not create form, as the form key not found.")

    # Post request: submit, validate, or save form
    if request.method == "POST":

        # Do not post form is login is required and user is not logged in
        if form.login_required:
            if not current_user.is_authenticated:
                return jsonify(error="Login required")

        req_json = request.get_json()

        # If object contains "save_session", save the values in session with key of `form key`
        if req_json.get("save_session"):
            session[form_key] = req_json.get("values")
            return jsonify(success="Saved form in session")

        # If form is validating token on page load
        if "validate_token" in req_json:
            return form.validate_token(req_json["validate_token"])
        else:
            # If posting form data to validation on submission
            if form.validate(req_json):
                # Return not the given data, but an edited version ex: changing country name to country code
                if len(form.edited_data) > 0:
                    return form.success(form.edited_data)
                return form.success(req_json)
            elif len(form.errors):  # failed with errors
                log_msg(request.url, f"{form_key} failed to validate, {form.errors[0]}")
                return form.failure()
            else:  # failed but no errors returned (shouldn't happen but can if form.errors list wasn't populated properly
                log_msg(request.url, f"{form_key} failed to validate, but no errors were given.")
                return form.failure()

    # Get request: send form requirements to front end to be built
    else:
        # Do not build form is login is required and user is not logged in
        if form.login_required:
            if not current_user.is_authenticated:
                return jsonify(error="Login required")

        return jsonify(form.build_form())
