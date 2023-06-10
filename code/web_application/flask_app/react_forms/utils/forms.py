import logging
from flask import current_app, session, jsonify
from email_validator import validate_email
from country_list import countries_for_language
from flask_login import current_user
from sqlalchemy import or_

from flask_app.utils.api.api import return_dict_user
from .base import ReactField, ReactForm
from flask_app.utils.api.api import return_dict_user
from flask_app.models import Tokens, Users, Logins, UserLog, ldb
from flask_app.utils.captcha import generate_math
from flask_app.utils.utils import set_current_query

########
# Email Field
########


class ReactEmailField(ReactField):
    """
    Universal Email Field
    * Check deliverability: see if the email bounces back (ex: sign up)
    * Check unique: if check unique disabled, will validate true check if email exists & if check unique enabled, will validate true if email does not exist
    """

    def __init__(
        self,
        required,
        label,
        name,
        suggest="off",
        check_deliverability=False,
        check_unique=False,
    ):
        super().__init__(label, name, suggest=suggest, required=required)
        self.type = "string"
        self.string_format = "email"
        self.placeholder = "example@email.com"
        self.min = 3
        self.max = 100
        self.check_deliverability = check_deliverability
        self.check_unique = check_unique

    def validate(self, data):
        super().validate(data)

        # Since validate email returns an error, check for the error
        # If there a better library for email checking?

        valid_email = True
        try:
            validate_email(data)
        except:
            valid_email = False

        if data and valid_email:
            user = Users.get_user_by_email(data)
            if self.check_unique:  # return false if email exists
                if user:
                    self.errors.append(
                        "This email is already associated with an account."
                    )
                    return False
            if not self.check_unique:  # return false if email does not exist
                if not user:
                    self.errors.append("This email is not associated with an account.")
                    return False
            if self.check_deliverability and current_app.config.get('EMAIL') and not current_app.config.get('TESTING'):  # check for email bounce
                try:
                    result = current_app.neverbounce.single_check(data)["result"]
                except Exception as e:
                    self.errors.append(f"Neverbounce Error: {e.__class__.__name__}: {e}")
                    return False
                if result != "valid":
                    self.errors.append("This email could not be verified")
                    return False
            return True
        self.errors.append("Not valid email address")
        return False


########
# React Password Field
########


class ReactPasswordField(ReactField):
    """
    React Universal Password Field
    """

    def __init__(
        self, label, name, ref_value_for="", suggest="new-password", required=False
    ):
        super().__init__(label, name, required=required, suggest=suggest)
        self.type = "string"
        self.string_format = "password"
        self.min = 8
        self.max = 999
        self.ref_value_for = ref_value_for


########
# React Number Field
########


class ReactNumberField(ReactField):
    """
    React Number Field
    """

    def __init__(
        self,
        label,
        name,
        min=-1,
        max=-1,
        default=0,
        required=False,
    ):
        super().__init__(label, name, required=required)
        self.type = "number"
        self.component = "number"
        self.default = default
        self.min = min
        self.max = max


########
# React String Array
########


class ReactStringArrayField(ReactField):
    """
    React String Array Field
    *  Takes optional autocomplete file name
    """

    def __init__(
        self,
        label,
        name,
        min=-1,
        max=-1,
        default=[],
        required=False,
        autocomplete="",
    ):
        super().__init__(label, name, required=required)
        self.type = "array"
        self.component = "stringArray"
        self.default = default
        self.min = min
        self.max = max
        self.autocomplete = autocomplete

    def get_dict(self):
        old_dict = super().get_dict()
        old_dict["autocomplete"] = self.autocomplete
        return old_dict


########
# React String Field
########


class ReactStringField(ReactField):
    """
    React String Field
    """

    def __init__(
        self,
        label,
        name,
        min_char=-1,
        max_char=-1,
        default="",
        ref_value_for="",
        required=False,
    ):
        super().__init__(label, name, suggest="off", required=required)
        self.type = "string"
        self.string_format = "text"
        self.default = default
        self.min = min_char
        self.max = max_char
        self.ref_value_for = ref_value_for


class ReactMathField(ReactStringField):
    """
    Universal CAPTCHA field, generates captcha React component
    * Property / component name will always be "math"
    """

    def __init__(self, required=True):
        super().__init__(
            label="Please answer with a digit", name="math", required=required
        )
        self.component = "math"

    def validate(self, data):
        try:
            if int(data) != int(session["math_answer"]):
                self.errors.append("Wrong CAPTCHA answer")
                return False
        except ValueError as e:
            self.errors.append("Please enter a digit into the Captcha field, rather than a spelled-out number.")
            return False
        return True

    def get_dict(self):
        old_dict = super().get_dict()

        # Create new question
        question, answer, text = generate_math()

        # Set new answer/question in session
        session["math_answer"] = answer
        session["math_question"] = text  # set text question in session

        # Add img to dictionary
        old_dict["img"] = question

        # TODO: Find out why this breaks
        # Get TTS link
        # audio_link = gtts_obj.say(lang="en-us", text=text)
        # old_dict["audio"] = audio_link[1:]
        old_dict["audio"] = ""
        return old_dict


class ToolRepresentationField(ReactStringField):
    """
    Representation of tool field, overriding the `ReactStringField` class

    * Specify the representation only for example `triples` or `paper_triples`
    """

    def __init__(
        self,
        default,
        label="representation",
        name="representation",
        min_char=-1,
        max_char=-1,
        ref_value_for="",
        required=False,
    ):
        super().__init__(
            label, name, min_char, max_char, default, ref_value_for, required
        )


class ReactActionField(ReactStringField):
    """
    TODO: ? make this its own field type, not string
    Representation of an action field, overriding the `ReactStringField` class

    * Action field required user to define valid actions, if the action is not one of those it is not valid
    """

    def __init__(
        self,
        default="",
        label="action",
        name="action",
        admin_actions=[],
        manager_actions=[],
        user_actions=[],
        min_char=-1,
        max_char=-1,
        ref_value_for="",
        required=True,
    ):
        self.admin_actions = admin_actions
        self.manager_actions = manager_actions
        self.user_actions = user_actions
        super().__init__(
            label, name, min_char, max_char, default, ref_value_for, required
        )

    def validate(self, data):
        if data in self.admin_actions and current_user.admin < 2:
            self.errors.append(
                "You cannot manage this user because you are not an admin"
            )
            return False
        if data in self.manager_actions and current_user.admin < 1:
            self.errors.append(
                "You cannot manage this user because you are not a manager"
            )
            return False
        if (
            data not in self.admin_actions
            and data not in self.manager_actions
            and data not in self.user_actions
        ):
            self.errors.append("This action does not exist")
            return False
        return True


########
# React Text Area Field
########


class ReactTextAreaField(ReactField):
    """
    Text Area Field
    """

    def __init__(
        self, label, name, min_char=-1, max_char=-1, default="", required=False
    ):
        super().__init__(label, name, required)
        self.type = "string"
        self.string_format = "text"
        self.component = "textarea"
        self.default = default
        self.min = min_char
        self.max = max_char


########
# React Select Field
########


class ReactSelectField(ReactField):
    """
    Select Field
    """

    def __init__(
        self, label, name, select_list, suggest="off", default="", required=False
    ):
        super().__init__(label, name, suggest=suggest, required=required)
        self.type = "string"
        self.string_format = "text"
        self.component = "select"
        self.default = default
        self.select_list = select_list
        self.min = 1
        self.max = 100

    def validate(self, data):
        if data == "" and self.required:
            self.errors.append("Select cannot have empty value since it is required")
            return False
        if data not in self.select_list:
            self.errors.append("Select field does not contain given data")
            return False
        return True

    def get_dict(self):
        old_dict = super().get_dict()
        old_dict.update(options=self.select_list)
        return old_dict


class ReactCountryField(ReactSelectField):
    """
    Country Field

    * Property name is country
    * Validation will change the given country to its country code
    """

    def __init__(self, label, name, default="", required=True):
        # Get list of countries
        countries = [country[1] for country in countries_for_language("en")]
        # Start with default field
        default = str(default)
        if default in countries:
            countries.remove(default)
        countries.insert(0, default)

        super().__init__(
            label,
            name,
            default=default,
            select_list=countries,
            required=required,
        )


class ReactPositionField(ReactSelectField):
    """
    Positions Field
    """

    def __init__(self, label, name, default="", required=True):
        position_list = [
            "Student",
            "Undergraduate",
            "Graduate",
            "Postdoctoral",
            "Professor",
            "Researcher",
            "Industry Worker",
            "Government Worker",
            "Other",
        ]
        if default in position_list:
            position_list.remove(default)
        position_list.insert(0, str(default))

        super().__init__(
            label,
            name,
            select_list=position_list,
            default=default,
            required=required,
        )


class ReactGrantField(ReactSelectField):
    """
    Positions Field
    """

    def __init__(self, label, name, default="", required=False):
        grant_list = [
            "Office of Behavioral and Social Sciences Research",
        ]
        if default in grant_list:
            grant_list.remove(default)
        grant_list.insert(0, str(default))

        super().__init__(
            label,
            name,
            select_list=grant_list,
            default=default,
            required=required,
        )


########
# React Token Field
########


class ReactTokenField(ReactField):
    """
    React Token Field

    On page reload, will make sure URL has valid token & validate again on submit
    """

    def __init__(self, required=True):
        super().__init__(label="", name="token", required=required)

    def validate(self, data):
        super().validate(data)
        user = Users.get_user_by_token(data)
        if not user:  # no user associated with this token
            self.errors.append("No user associated with token")
            return False
        return True


########
# React Checkbox Field
########


class ReactCheckBoxField(ReactField):
    def __init__(self, label, name, default, required=False):
        super().__init__(label=label, name=name, required=required)
        self.default = default
        self.type = "boolean"
        self.component = "checkbox"

    def validate(self, data):
        # If there is no data / false data and field is required
        if not data and self.required:
            self.errors.append(f"Please agree to the {self.name} field")
            return False
        if data == False and self.required:
            self.errors.append(f"Please agree to the {self.name} field")
            return False
        return True


########
# Auth Forms
########


class ReactVerifyEmailForm(ReactForm):
    """
    React Verify Email Form
    """

    def __init__(self):
        super().__init__()
        self.key = "verify_email_form"
        self.fields = [
            ReactTokenField(),
        ]

    def success(self, data):
        user = Users.get_user_by_token(data["token"])
        user.set_verified(True)
        UserLog.record_change(user, user, action="email verified")
        Tokens.delete_token(data["token"])
        return jsonify(success=user.email)

    def validate_token(self, token):
        token_user = Users.get_user_by_token(token)
        # No user associated with this token
        if not token_user:
            logging.error("User cannot be found with this error")
            return jsonify(error="This verification link cannot be found.")
        logging.error("Token is invalid")
        return jsonify(success="Token is valid")


class ReactRequestVerificationEmailForm(ReactForm):
    """
    React Request Verify Email Form
    """

    def __init__(self):
        super().__init__()
        self.key = "request_email_verification_form"
        self.fields = [
            ReactMathField(),
            ReactEmailField(label="Email address", name="email", required=True),
        ]
        self.validators = [self.check_user_has_email_verified]

    def success(self, data):
        user = Users.get_user_by_email(data["email"])
        if current_app.config['EMAIL']:
            err = user.send_email_verification()
            if err: return jsonify(error=str(err))
            return jsonify(success=user.email)
        else:
            return jsonify(error="Sending email has been disabled for this application. If you would like this feature, please modify your configuration to enable emailing.")

    def check_user_has_email_verified(self, data):
        user = Users.get_user_by_email(data["email"])
        if not user:
            self.errors.append("This email is not associated with an account")
            return False
        if user.verified:  # check if they are already verified
            self.errors.append("This email is already verified")
            return False
        return True


class ReactResetPasswordForm(ReactForm):
    """
    React Reset Password Form
    """

    def __init__(self):
        super().__init__()
        self.key = "reset_password_form"
        self.fields = [
            ReactPasswordField(
                label="Enter new password", name="password", required=True
            ),
            ReactPasswordField(
                label="Confirm password",
                name="confirm",
                ref_value_for="password",
                required=True,
            ),
            ReactTokenField(),
        ]

    def success(self, data):
        user = Users.get_user_by_token(data["token"])
        user.set_password(
            data["password"], True
        )  # update password and commit to database
        UserLog.record_change(user, user, action="password reset")
        # user.login()  # log them in
        Tokens.delete_token(data["token"])  # delete this token
        return jsonify(success=user.email)

    def validate_token(self, token):
        token_user = Users.get_user_by_token(token)
        if not token_user:  # no user associated with this token
            return jsonify(error="This verification link cannot be found.")
        return jsonify(success="Token is valid")


class ReactForgotPasswordForm(ReactForm):
    """
    React Forgot Password Form
    """

    def __init__(self):
        super().__init__()
        self.key = "forgot_password_form"
        self.fields = [
            ReactMathField(),
            ReactEmailField(label="Email address", name="email", required=True),
        ]
        self.validators = [self.user_exists_not_banned]

    def success(self, data):
        user = Users.get_user_by_email(data["email"])
        if current_app.config['EMAIL']:  # sending email enabled
            err = user.send_password_reset_email()
            if err:
                return jsonify(error=str(err))
            return jsonify(success=user.email)
        else:  # sending email is disabled
            return jsonify(error="Sending email has been disabled for this application, so passwords may not be reset. If you would like this feature, please modify your configuration to enable emailing.")

    def user_exists_not_banned(self, data):
        user = Users.get_user_by_email(data["email"])
        if not user:  # if no user exists with this email
            self.errors.append("Unknown email")
            return False
        if not user.active:  # banned account
            self.errors.append(
                "This account has been suspended. You may not reset your password."
            )
            return False
        if not user.verified:  # check whether this email is verified
            self.errors.append(
                f"For your security, you may not change your password before verifying your email. If are unable to verify your email because you forgot your password, please contact support at {current_app.config['EMAIL_ADDRESS']}"
            )
            return
        return True


class ReactLoginForm(ReactForm):

    """
    React Login Form
    """

    def __init__(self):
        super().__init__()
        self.key = "sign_in_form"
        self.fields = [
            ReactEmailField(
                label="Email address", name="email", required=True, suggest="on"
            ),
            ReactPasswordField(
                label="Password", name="password", required=True, suggest="on"
            ),
        ]
        self.validators = [self.legit_validate_attempt, self.check_email_password]

    def success(self, data):
        user = Users.get_user_by_email(data["email"])
        user.login()
        return jsonify(success=return_dict_user(user))

    # def validate(self, data):
    #     # Check for attempts with IP

    #     # Basic validation
    #     if not self.basic_validation():
    #         return False

    #     return True

    def legit_validate_attempt(self, data):
        """
        Verifies that the request is legit and logs login attempts
        """
        email = data["email"]
        user = Users.get_user_by_email(email)

        # If email is associated with account and they are verified, then unverify account
        same_email = Logins.get_email_attempts(email)
        if same_email.count() > 5:
            Logins.record(email, user, False, "Too many attempts for same email")
            if current_app.config['EMAIL']:  # if emailing enabled
                if user and user.verified:  # if user is verified
                    user.verified = False  # Un-verify email
                    UserLog.record_change(user, None, "locked at login")
                    user.send_locked_account_email()
                self.errors.append("Too many attempts - this account has been locked. An email has been sent with instructions to unlock your account.")
            else:  # emailing disabled
                self.errors.append("Too many attempts - please try again in one minute.")
            return False

        # If email is coming from same ip address and attempted user is not verified
        same_ip = Logins.get_ip_attempts()  # all attempts from this IP
        if same_ip.count() > 5:  # Too many attempts from the same ip
            Logins.record(email, user, False, "Too many attempts from same IP")
            self.errors.append("Too many attempts - please try again in one minute.")
            return False
        return True

    def check_email_password(self, data):
        """
        Extend validation to check database for email and password.
        """

        email = data["email"]
        password = data["password"]
        user = Users.get_user_by_email(email)

        # Check email/password
        if not user:  # If no user exists with this email
            self.errors.append("Your email or password is incorrect")
            Logins.record(email, None, False, "unknown email")
            return False
        if not user.check_password(password):  # Check password
            self.errors.append("Your email or password is incorrect")
            Logins.record(email, user, False, "incorrect password")
            return False

        # Check if banned account
        if not user.active:
            self.errors.append("This account has been suspended.")
            Logins.record(email, user, False, "banned")
            return False

        # Check if verified account
        if not user.verified:
            self.errors.append("You must verify your email before logging in.")
            Logins.record(email, user, False, "not verified")
            return False

        return True


class ReactSignUpForm(ReactForm):
    """
    React Sign Up Form
    """

    def __init__(self):
        super().__init__()
        self.key = "sign_up_form"
        self.fields = [
            ReactMathField(),
            ReactStringField(label="Name", name="name", required=True),
            ReactEmailField(
                label="Email address",
                name="email",
                required=True,
                check_deliverability=True,
                check_unique=True,
            ),
            ReactPasswordField(label="Password", name="password", required=True),
            ReactPasswordField(
                label="Confirm password",
                name="confirm",
                ref_value_for="password",
                required=True,
            ),
            ReactStringField(label="Company", name="company", required=True),
            ReactCountryField(
                label="Country",
                name="country",
                required=True,
                default="",
            ),
            ReactPositionField(
                label="Position",
                name="position",
                required=True,
                default="",
            ),
            ReactStringField(
                label="Department",
                name="department",
            ),
            ReactTextAreaField(label="Why Brainworks?", name="purpose"),
            ReactCheckBoxField(
                label="Terms of service", name="terms", default=False, required=True
            ),
        ]

        self.validators = []

    def success(self, data):
        user = Users.new_user2(self.edited_data)  # create new user from this form
        UserLog.record_change(user, user, action="signup")  # record new user in log
        if current_app.config['EMAIL']:  # email enabled
            return jsonify(success=f"Success!",
                           email=user.email,
                           instructions=f"An email has been sent to {user.email}. Please follow the link inside to verify your account before signing in. If you don't receive the email within 5 minutes, check your spam folder. Otherwise, request another email by clicking below.")
        else:  # email disabled
            return jsonify(success="Success!",
                           email=user.email,
                           instructions=f"Since sending email has been disabled for this application, you are NOT required to verify your email before logging in. If you would like this feature, please configure the application to enable sending email.")

    def validate(self, data):

        # Basic validation
        if not self.basic_validation(data):
            return False

        # If country exist, set value equal to country code
        country_found = False
        for tuple in countries_for_language("en"):
            if data["country"] in tuple:
                data["country"] = tuple[0]
                self.edited_data = data
                return True
        if not country_found:
            self.errors.append("Not a valid country given")
            return False

        # Check for matching password fields
        if data["password"] != data["confirm"]:
            self.errors.append("Password and confirm password do not match")
            return False

        return True


########
# Profile Edit Forms
########


class ReactProfileEditPassword(ReactForm):
    """
    React Profile Edit for Changing Your Password
    """

    def __init__(self):
        super().__init__()
        self.login_required = True
        self.key = "profile_edit_password_form"
        self.fields = [
            ReactPasswordField(label="Current password", name="old", required=True),
            ReactPasswordField(label="New password", name="password", required=True),
            ReactPasswordField(
                label="Confirm password",
                name="confirm",
                ref_value_for="password",
                required=True,
            ),
        ]
        self.validators = [self.password_validate]

    def password_validate(self, data):
        is_valid = True

        # Check if old password given is actually the old password
        if not current_user.check_password(data["old"]):
            self.errors.append("Current password is not correct")
            is_valid = False

        # Check new and confirm password fields, so they match
        if data["password"] != data["confirm"]:
            self.errors.append("New password and confirm password do not match")
            is_valid = False

        return is_valid

    def success(self, data):
        user = Users.get_user_by_email(current_user.email)
        user.update_profile_password(data["password"])
        return jsonify(success="Password successfully changed")


class ReactProfileEditEmail(ReactForm):
    """
    React Profile Edit for Changing Account Email
    """

    def __init__(self):
        super().__init__()
        self.login_required = True
        self.key = "profile_edit_email_form"
        self.fields = [
            ReactEmailField(
                label="Enter new email address",
                name="email",
                required=True,
                check_deliverability=True,
                check_unique=True,
            ),
            ReactPasswordField(label="Enter password", name="password", required=True),
        ]
        self.validators = [self.new_email_validate]

    def new_email_validate(self, data):
        is_valid = True

        # Check if given password is the user's password
        if not current_user.check_password(data["password"]):
            self.errors.append("Current password is not correct")
            is_valid = False

        # Check if given email is different from current one
        if data["email"] == current_user.email:
            self.errors.append("New email is the same as the current email")
            is_valid = False

        return is_valid

    def success(self, data):
        user = Users.get_user_by_email(current_user.email)
        user.update_profile_email(data["email"])
        # "verify" is whether the user needs to verify their new email. If false, they won't get a popup telling them to do so.
        return jsonify(success=return_dict_user(current_user), verify=current_app.config['EMAIL'])


class ReactProfileEditDetails(ReactForm):
    """
    React Profile Edit for Account Details
    """

    def __init__(self):
        super().__init__()
        self.login_required = True
        self.key = "profile_edit_details_form"
        if not current_user.is_authenticated:
            self.fields = []
        else:
            self.fields = [
                ReactStringField(
                    label="Name", name="name", required=True, default=current_user.name
                ),
                ReactStringField(
                    label="Company",
                    name="company",
                    required=True,
                    default=current_user.company,
                ),
                ReactCountryField(
                    label="Country",
                    name="country",
                    required=True,
                    default=current_user.country,
                ),
                ReactPositionField(
                    label="Position",
                    name="position",
                    required=True,
                    default=current_user.position,
                ),
                ReactStringField(
                    label="Department",
                    name="department",
                    default=current_user.department,
                ),
                ReactTextAreaField(
                    label="Why Brainworks?",
                    name="purpose",
                    default=current_user.purpose,
                ),
            ]
        self.validators = [self.check_for_changes]

    def check_for_changes(self, data):
        # Check if user has made any changes
        if (
            current_user.name == data.get("name")
            and current_user.country == data.get("country")
            and current_user.company == data.get("company")
            and current_user.position == data.get("position")
            and current_user.department == data.get("department")
            and current_user.purpose == data.get("purpose")
        ):
            self.errors.append("No profile details were changed")
            return False
        return True

    def success(self, data):
        user = Users.get_user_by_email(current_user.email)
        user.update_profile_details(data)
        return jsonify(success=return_dict_user(current_user))


########
# Admin Forms
########


class ReactUserSearchForm(ReactForm):
    """
    React User Search Form
    """

    def __init__(self):
        super().__init__()
        self.login_required = True
        self.admin_level = 1
        self.key = "search_user_form"
        self.fields = [
            ReactStringField(
                label="",
                name="query",
                required=False,
            ),
            ReactNumberField(label="", name="page", required=True),
        ]

    def validate(self, data):

        # Check for basic validation
        if not self.basic_validation(data):
            return False

        # ? Temp add this to the base class
        if current_user.admin < 1:
            self.errors.append("Not a manager or admin")
            return False

        return True

    def success(self, data):
        query = data.get("query")
        page = data.get("page")

        user_dicts = []
        users = (
            Users.query.filter(
                or_(
                    Users.name.contains(query),
                    Users.email.contains(query),
                    Users.id == query,
                )
            )
            .order_by(Users.name)
            .limit(10)
            .all()
            # .paginate(page=page, per_page=10)
        )
        for user in users:
            user_dicts.append(return_dict_user(user))
            # user_dicts.append(
            #     {
            #         "name": user.name,
            #         "admin": user.admin,
            #         "active": user.active,
            #         "email": user.email,
            #     }
            # )
        return jsonify(success={"users": user_dicts})


class ReactManagerUserForm(ReactForm):
    """
    React Manager User Form
    """

    def __init__(self):
        super().__init__()
        self.login_required = True
        self.key = "manage_user_form"
        self.fields = [
            ReactActionField(
                manager_actions=[
                    "manual verification",
                    "manual un-verification",
                    "send verification",
                    "reset tutorial",
                ],
                admin_actions=[
                    "banned",
                    "un-banned",
                    "promoted",
                    "demoted",
                    "deleted",
                ],
            ),
            ReactStringField(
                label="",
                name="target_user",
                required=True,
            ),
        ]

    def validate(self, data):

        # Check for basic validation and user permission given action
        if not self.basic_validation(data):
            return False

        # Check if targeted user exists
        target_user = Users.get_user_by_email(data.get("target_user"))
        if not target_user:
            self.errors.append("Targeted user does not exist")
            return False

        # Check to make sure user can't delete or ban themselves
        action = data.get("action")
        if current_user.id == target_user.id and action in ["banned", "un-banned", "promoted", "demoted", "deleted"]:
            self.errors.append("You cannot preform this action on yourself!")
            return False

        return True

    def success(self, data):
        action = data.get("action")
        target_user = Users.get_user_by_email(data.get("target_user"))

        if action == "manual verification":
            target_user.verified = True
        if action == "manual un-verification":
            target_user.verified = False
        if action == "send verification":
            target_user.send_email_verification()
        if action == "reset tutorial":
            target_user.tutorial = False
        if action == "banned":
            target_user.active = False
        if action == "un-banned":
            target_user.active = True
        if action == "promoted":
            target_user.admin = 1
        if action == "demoted":
            target_user.admin = 0
        if action == "deleted":
            target_user.delete()

        try:
            UserLog.record_change(
                target_user, current_user, action=action
            )  # Record change made by current_user
            ldb.session.commit()  # Commit changes to database
        except Exception as e:
            logging.error(e)
        return jsonify(success=return_dict_user(target_user))


########
# Tool Forms
########


class ReactToolTemplateForm(ReactForm):
    """
    React Tool Template Form

    Superclass for all tool forms
    """

    def __init__(self):
        super().__init__()
        self.login_required = True

    def success(self, data):
        """
        If all data if valid, set current query in session
        """
        set_current_query(data)
        return jsonify(
            success="Now building your visualizer. This may take a while, please do not leave the page."
        )

    def validate(self, data):
        if not self.basic_validation(data):
            return False

        return True


class ReactTriplesForm(ReactToolTemplateForm):
    """
    React Triples Form
    """

    def __init__(self):
        super().__init__()
        self.key = "tool_triples_form"
        self.fields = [
            ToolRepresentationField(default="triples"),
            ReactStringArrayField(
                label="Include Unified Medical Language System concepts",
                name="include_concepts",
                required=True,
                autocomplete="umls_concepts",
            ),
            ReactStringArrayField(
                label="Exclude concepts",
                name="exclude_concepts",
                required=False,
                default=["Increase", "Increased", "Levels (qualifier value)", "High"],
                autocomplete="umls_concepts",
            ),
            ReactNumberField("Node limit", name="limit", required=False, default=300),
        ]

    def validate(self, data):
        if not super().validate(data): return False

        # check if there are items in both include and exclude.
        if len(set(data['exclude_concepts']).intersection(set(data['include_concepts']))) > 0:
            self.errors.append("You have selected terms that are excluded from your search. Please use the Advanced search to see excluded terms.")
            return False

        return True


class ReactPaperTriplesForm(ReactToolTemplateForm):
    """
    React Paper Triples Form
    """

    def __init__(self):
        super().__init__()
        self.key = "tool_paper_triples_form"
        self.fields = [
            ToolRepresentationField(default="paper_triples"),
            ReactStringField(
                label="Pub Med ID",
                name="pmid",
                required=True,
            ),
        ]


class ReactPaperCitationsForm(ReactToolTemplateForm):
    """
    React Paper Citations Form
    """

    def __init__(self):
        super().__init__()
        self.key = "tool_paper_citations_form"
        self.fields = [
            ToolRepresentationField(default="paper_citations"),
            ReactStringArrayField(
                label="Include Unified Medical Language System concepts",
                name="include_concepts",
                required=True,
                autocomplete="umls_concepts",
            ),
            ReactNumberField("Node limit", name="limit", required=False, default=200),
        ]


class ReactTopicCoOccurencesForm(ReactToolTemplateForm):
    """
    React Topic Co-occurrences
    """

    def __init__(self):
        super().__init__()
        self.key = "tool_topic_co_occurrences_form"
        self.fields = [
            ToolRepresentationField(default="topic_co_occurrences"),
            ReactStringArrayField(
                label="Exclude Medical Subject Headings concepts",
                name="exclude_mesh_concepts",
                required=False,
                default=["Humans", "Animals"],
                autocomplete="mesh_concepts",
            ),
            ReactStringArrayField(
                label="Include Medical Subject Headings concepts",
                name="include_mesh_concepts",
                required=True,
                autocomplete="mesh_concepts",
            ),
            ReactNumberField("Approximate Graph Size", name="limit", required=False, default=100),
        ]

    def validate(self, data):
        if not super().validate(data): return False

        # check if there are items in both include and exclude.
        if len(set(data['exclude_mesh_concepts']).intersection(set(data['include_mesh_concepts']))) > 0:
            self.errors.append("You have selected terms that are excluded from your search. Please use the Advanced search to see excluded terms.")
            return False

        return True