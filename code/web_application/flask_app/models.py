from flask import current_app, request
from flask_login import current_user, login_user
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_utils import (
    EmailType,
    PasswordType,
    PhoneNumberType,
    CountryType,
    UUIDType,
)
from sqlalchemy.sql import exists

from datetime import datetime, timedelta
import logging
from uuid import uuid4

from flask_app import ldb  # user db
from flask_app.utils.mail.mail import (
    send_mail,
    VERIFY_EMAIL_BODY,
    CHANGE_PASSWORD_BODY,
    LOCKED_ACCOUNT_BODY,
)
from country_list import countries_for_language


"""
IF MODIFYING THESE SCHEMAS:

1. Perform a `flask db migrate -m "message"` to create the migration scripts
2. Go double-check the new script in migrations/versions/
3. Run `flask db upgrade` to upgrade your local database according to that script.
4. If you are unsure about the script, instead use `flask db upgrade --sql` to triple-check the raw SQL.
5. Test
6. push to production
7. The production server will automatically upgrade according to that script when deployed
"""


class Users(ldb.Model):
    """
    User table model.
    Accessed in all jinja templates with current_user.

    IMPORTANT
    When changing this model, if you make a change that affects any related website forms,
        you must change the methods Users.from_form() and Users.populate_form() accordingly.

    ALSO IMPORTANT:
    Methods prefixed with _ are not meant to be called outside the class.
    This is because these methods make changes to the user object, but DONT COMMIT to the database.
    Therefore they are meant to be used internally and must have a session.commit() call afterward.
    All methods which are meant to be used externally will commit if they make changes, so commit()
        should never have to be called outside this class.
    """

    __tablename__ = "brainworks-users"
    # Database column definitions
    id = ldb.Column(ldb.Integer, primary_key=True)
    name = ldb.Column(ldb.String(50))
    email = ldb.Column(EmailType(100), index=True, unique=True, nullable=False)
    password = ldb.Column(ldb.String(255), nullable=False)

    # company info
    company = ldb.Column(ldb.String(100), nullable=False)
    department = ldb.Column(ldb.String(50))
    position = ldb.Column(ldb.String(20))
    phone = ldb.Column(PhoneNumberType)
    country = ldb.Column(CountryType, nullable=False)
    purpose = ldb.Column(ldb.String(200))

    # not given by user
    admin = ldb.Column(ldb.Integer)  # Admin Level. 0 = user, 1 = manager, 2 = admin.
    active = ldb.Column(ldb.Boolean, default=True)  # whether the account is active
    verified = ldb.Column(ldb.Boolean)  # email verified
    created = ldb.Column(ldb.DateTime)  # account creation date
    last_login = ldb.Column(ldb.DateTime)  # updated on each login
    tutorial = ldb.Column(
        ldb.Boolean, default=False
    )  # whether the user has had the tutorial

    # properties (NOT DATABASE COLUMNS) required by Flask Login
    is_anonymous = False

    @property
    def is_authenticated(self):
        """Used by FlaskLogin to check whether a user is authenticated"""
        return self.is_active

    @property
    def is_active(self):
        """Used by FlaskLogin to check account active status"""
        return self.active

    def login(self):
        """
        Logs in the user through Flask-Login and saves login time.
        COMMITS TO DATABASE.
        """
        login_user(self, remember=False)
        self.last_login = datetime.utcnow()  # mark login time
        Logins.record(self.email, self, True)  # record successful login
        ldb.session.commit()

    def get_id(self):
        """Required for Flask Login"""
        return str(self.id)

    def get_name(self, full=False):
        """Output a formatted string with the user's name."""
        if full:
            return self.name
        else:
            return " ".join(self.name.split(" ")[:3])

    def set_tutorial(self, boolean):
        """Sets the tutorial status of the user"""
        self.tutorial = boolean
        ldb.session.commit()  # commit new user to database

    def get_permissions(self):
        """Display user permissions"""
        if not self.admin or self.admin <= 0:  # 0 or None
            return "User"
        elif self.admin == 1:
            return "Manager"
        else:  # >= 2
            return "Admin"

    def set_verified(self, boolean):
        """Set verified status of user"""
        self.verified = boolean
        ldb.session.commit()

    def set_password(self, password, commit=False):
        """
        Set user hashed password.
        COMMITS ONLY IF <commit> = True
        """
        if password:
            self.password = generate_password_hash(password, method="sha256")

        if commit:
            ldb.session.commit()

    def check_password(self, hashed):
        """Check hashed password against an unknown hash"""
        return check_password_hash(self.password, hashed)

    def set_country_as_code(self, country):
        # ? Is this needed?
        """If country is exists, give it's country code"""
        set_as_code = False
        for tuple in countries_for_language("en"):
            if country in tuple:
                self.country = tuple[0]
                set_as_code = True
        if not set_as_code:
            self.country = country

    #### Send Emails
    def send_email_verification(self):
        """
        Send an email verification this user.
        COMMITS TO DATABASE
        """
        if not current_app.config['EMAIL']:  # if email sending is disabled
            return

        token = Tokens.create_token(self)  # create new token for this user
        Tokens.clear_expired()  # clear expired tokens

        verify_link = (
            current_app.config["DOMAIN_NAME"] + "/verify-email/" + str(token.token)
        )

        logging.info("Verification link created at: " + verify_link)

        # Don't send mail if running in unit test
        if current_app.config["TESTING"]:
            return

        err = send_mail(
            subject="BRAINWORKS: Verify Email",
            recipient=[self.email],
            body_text=VERIFY_EMAIL_BODY.format(name=self.name, verify_link=verify_link),
        )
        logging.info(f"Sending verification email to: {self.email}")
        if err:  # an err occurred while sending mail
            logging.error(
                f"Error sending email verification to: {self.email}.\n Error: {err.__class__.__name__}: {err}"
            )
            return err

    def send_password_reset_email(self):
        """ Send a password reset email to this user """
        if not current_app.config['EMAIL']:  # if email sending is disabled
            return

        token = Tokens.create_token(self)  # create new token for this user
        Tokens.clear_expired()  # clear expired tokens

        reset_link = (
            current_app.config["DOMAIN_NAME"] + "/reset-password/" + str(token.token)
        )

        logging.info("Reset link created at: " + reset_link)

        # Don't send mail if running in unit test
        if current_app.config["TESTING"]:
            return

        err = send_mail(
            subject="BRAINWORKS: Change Password Request",
            recipient=[self.email],
            body_text=CHANGE_PASSWORD_BODY.format(
                name=self.name, reset_link=reset_link
            ),
        )

        if err:  # an err occurred while sending mail
            logging.error(
                f"Error sending password reset email to: {self.email}.\n Error: {err.__class__.__name__}: {err}"
            )
            return err
        else:
            logging.info(f"Sending password reset email to: {self.email}")

    def send_locked_account_email(self):
        """
        Send an email verification this user after their account was locked at login.
        COMMITS TO DATABASE
        """
        if not current_app.config['EMAIL']:  # if email sending is disabled
            return

        token = Tokens.create_token(self)  # create new token for this user
        Tokens.clear_expired()  # clear expired tokens

        verify_link = (
            current_app.config["DOMAIN_NAME"] + "/unlock-account/" + str(token.token)
        )

        # Don't send mail if running in unit test
        if current_app.config["TESTING"]:
            return

        err = send_mail(
            subject="BRAINWORKS: Account Locked",
            recipient=[self.email],
            body_text=LOCKED_ACCOUNT_BODY.format(
                name=self.name, verify_link=verify_link
            ),
        )

        logging.info("Verification created at: " + verify_link)

        logging.info(f"Sending verification email to: {self.email}")
        if err:  # an err occurred while sending mail
            logging.error(
                f"Error sending email verification to: {self.email}.\n Error: {err.__class__.__name__}: {err}"
            )
            return err

    ### Manage Accounts
    def update_profile(self, form):
        """
        Update a user's profile from a form.
        Returns whether anything changed.
        """
        old_email = self.email  # previous email
        self.from_form(form)  # update from form

        if ldb.session.is_modified(
            self
        ):  # the user is now different from the user in the database
            ldb.session.flush()
            # changing email (or creating one on signup), and email sending is enabled
            if old_email != self.email and current_app.config['EMAIL']:
                self.verified = False  # no longer verified
                self.send_email_verification()

            ldb.session.commit()  # commit new user to database
            return True
        return False

    def update_profile_password(self, new_password):
        ldb.session.flush()
        self.set_password(new_password)
        ldb.session.commit()

    def update_profile_email(self, new_email):
        self.email = new_email
        if current_app.config['EMAIL']:  # if emailing enabled, user must verify email
            self.verified = False
            self.send_email_verification()
        else:  # if emailing disabled, automatically verify
            self.verified = True
        ldb.session.commit()

    def update_profile_details(self, details):
        self.name = details.get("name")
        self.company = details.get("company")
        self.department = details.get("department")
        self.position = details.get("position")
        self.set_country_as_code(details.get("country"))
        self.purpose = details.get("purpose")
        ldb.session.commit()

    def from_form(self, form):
        """Update the user with the form data."""
        self.name = form.name.data
        self.company = form.company.data
        self.department = form.department.data
        self.position = form.position.data
        self.phone = form.phone.data
        self.country = form.country.data
        self.purpose = form.purpose.data
        self.set_password(form.password.data)  # hash password
        self.email = form.email.data

    def populate_form(self, form):
        """Populate the form fields with values from the current user"""
        form.email.data = self.email
        form.name.data = self.name
        form.company.data = self.company
        form.department.data = self.department
        form.position.data = self.position
        form.phone_input.data = (
            self.phone.e164 if self.phone else None
        )  # get full international number if user has one
        form.country.data = self.country
        form.purpose.data = self.purpose

    def delete(self):
        """Delete this user and add it to the archive table"""
        a_user = UserArchive()  # create new archived user

        a_user.id = self.id
        a_user.company = self.company
        a_user.department = self.department
        a_user.position = self.position
        a_user.phone = self.phone
        a_user.country = self.country
        a_user.purpose = self.purpose
        a_user.created = self.created
        a_user.last_login = self.last_login

        ldb.session.add(a_user)  # add archived user
        ldb.session.delete(self)  # delete this user
        ldb.session.commit()

    def record_change(self, performed_user=None, action=None):
        """Records a change in the user-log table"""
        UserLog.record_change(self, performed_user, action)

    def __repr__(self):
        return f"ID: {self.id} | Email: {self.email}"

    @staticmethod
    def new_user2(json):
        """
        Create a new user from the given form.
        Used in the signup page.
        COMMITS TO DATABASE
        """
        user = Users()  # create new user
        user.created = datetime.utcnow()  # Current UTC time
        user.active = True  # set active to true by default

        # if emailing is enabled, users are unverified by default
        if current_app.config['EMAIL']:
            user.verified = False
        else:  # if emailing disabled, users are always verified
            user.verified = True

        """ Update the user with the form data. """
        user.name = json["name"]
        user.company = json["company"]
        user.department = json["department"]
        user.position = json["position"]
        user.phone = ""
        user.country = json["country"]
        user.purpose = json["purpose"]
        user.set_password(json["password"])  # hash password
        user.email = json["email"]

        # Add the new user
        ldb.session.add(user)

        ldb.session.commit()

        # Send email to user
        user.send_email_verification()
        return user

    @staticmethod
    def new_user(form):
        """
        Create a new user from the given form.
        Used in the signup page.
        COMMITS TO DATABASE
        """

        user = Users()  # create new user
        user.created = datetime.utcnow()  # Current UTC time
        user.active = True  # set active to true by default

        # if emailing is enabled, users are unverified by default
        if current_app.config['EMAIL']:
            user.verified = False
        else:  # if emailing disabled, users are always verified
            user.verified = True

        user.from_form(form)  # get data from form

        # Add the new user
        ldb.session.add(user)
        ldb.session.commit()

        # Send verification email
        user.send_email_verification()
        return user

    @staticmethod
    def get_user_by_email(email):
        """Returns the user associated with the given email, or None"""
        return Users.query.filter_by(email=email).first()

    @staticmethod
    def get_user_by_id(id):
        """Returns the user associated with the given id, or None"""
        return Users.query.filter_by(id=id).first()

    @staticmethod
    def get_user_by_token(token):
        """Get the user associated with the given token, if they exist"""
        try:
            token = Tokens.query.filter_by(
                token=token
            ).first()  # get the table row for this token
        except:
            return

        if not token:  # this token doesn't exist
            return

        user = Users.get_user_by_id(token.user_id)  # get the associated user
        if not user:
            logging.error(f"User doesn't exist for the token: {token}")
            return
        return user  # return user object

    @staticmethod
    def set_admin(email, level):
        """
        Given a user's email, set their admin level.
        0 = Regular user
        1 = Manager
        2 = Admin
        """
        try:
            allowed = [0, 1, 2]
            assert level in allowed, f"User admin level must be in: {allowed}"
            user = Users.get_user_by_email(email)
            assert user, f'Could not find a user with the email "{email}"'
            assert (
                user.verified
            ), f'The user "{user.name}" has not verified their email.'
            user.admin = level
            user.active = True
            UserLog.record_change(user)  # record changes
            ldb.session.commit()
            msg = f"Set admin level {level} of user: {user}"
            print(msg)
            logging.info(msg)
        except Exception as e:
            msg = f"Error: {e.__class__.__name__}: {e}"
            print(msg)
            logging.error(msg)


class UserArchive(ldb.Model):
    """Table for deleted users"""

    __tablename__ = "user-archive"

    # Database column definitions
    id = ldb.Column(
        ldb.Integer, primary_key=True, autoincrement=False
    )  # the user ID deleted
    company = ldb.Column(ldb.String(100), nullable=False)
    department = ldb.Column(ldb.String(50))
    position = ldb.Column(ldb.String(20))
    country = ldb.Column(CountryType, nullable=False)
    purpose = ldb.Column(ldb.String(200))
    created = ldb.Column(ldb.DateTime)  # account creation date
    last_login = ldb.Column(ldb.DateTime)  # updated on each login


class UserLog(ldb.Model):
    """
    Model for the User Log table.
    Records a history of all user profile information.
    """

    __tablename__ = "user-log"

    # Database column definitions
    log_id = ldb.Column(ldb.Integer, primary_key=True, autoincrement=True)
    user_id = ldb.Column(ldb.Integer, nullable=False)  # user ID
    who_id = ldb.Column(ldb.Integer)  # user ID of the user that made the change.
    date = ldb.Column(ldb.DateTime, nullable=False)  # date of this change.
    action = ldb.Column(ldb.String(50))  # action taken

    # New profile information.
    name = ldb.Column(ldb.String(50))
    email = ldb.Column(EmailType(100))
    phone = ldb.Column(PhoneNumberType)
    password = ldb.Column(ldb.String(255))
    company = ldb.Column(ldb.String(100))
    department = ldb.Column(ldb.String(50))
    position = ldb.Column(ldb.String(20))
    country = ldb.Column(CountryType)
    purpose = ldb.Column(ldb.String(200))

    admin = ldb.Column(ldb.Integer)  # Admin Level. 0 = user, 1 = manager, 2 = admin.
    active = ldb.Column(ldb.Boolean)  # whether the account is active
    verified = ldb.Column(ldb.Boolean)  # email verified
    tutorial = ldb.Column(ldb.Boolean)  # whether the user has had the tutorial

    @staticmethod
    def record_change(user, performed_user=None, action=None):
        """
        Record the current state of a user in this table.
        Whenever a user's information is changed, make sure to call this method.
        <user> is the Users object that just changed
        <performed_user> is the Users object that made the change.

        Commits the new record.
        """
        if action:
            action = action[:50]  # truncate if over 50 char limit

        try:
            record = UserLog()  # create new record (row in the table)

            record.user_id = user.id
            record.who_id = performed_user.id if performed_user else None
            record.date = datetime.utcnow()  # Current UTC time
            record.action = action

            record.name = user.name
            record.email = user.email
            record.phone = user.phone
            record.password = user.password
            record.company = user.company
            record.department = user.department
            record.position = user.position
            record.country = user.country
            record.purpose = user.purpose

            record.admin = user.admin
            record.active = user.active
            record.verified = user.verified
            record.tutorial = user.tutorial

            ldb.session.add(record)
            ldb.session.commit()  # commit new record to database
        except Exception as e:
            logging.error(
                f"Failed to save log record for action {action}. {e.__class__.__name__}: {e}"
            )
            ldb.session.rollback()

    @staticmethod
    def initialize():
        """
        Initialize all current users in the users table into the user-log table.
        Was only used once when the user-log table was added.
        """
        # get users not already in the user log
        users = Users.query.filter(~exists().where(UserLog.user_id == Users.id))
        for user in users:
            UserLog.record_change(user, action="init")


class Logins(ldb.Model):
    """
    Model for the login-attempts table
    """

    __tablename__ = "login-attempts"

    # Database column definitions
    id = ldb.Column(ldb.Integer, primary_key=True)
    email = ldb.Column(
        ldb.String(100)
    )  # what was input as the email (even if not valid)
    user_id = ldb.Column(
        ldb.Integer
    )  # user ID matched to email, or None if no user was matched
    date = ldb.Column(ldb.DateTime, nullable=False)  # date of the login attempt
    success = ldb.Column(
        ldb.Boolean, nullable=False
    )  # whether they successfully logged in
    reason = ldb.Column(ldb.String(50))  # reason for an unsuccessful login

    ip = ldb.Column(ldb.String(15))  # IP address
    platform = ldb.Column(ldb.String(20))  # device platform
    browser = ldb.Column(ldb.String(20))  # browser used
    version = ldb.Column(ldb.String(10))  # browser version

    time_threshold = 60  # 60 second threshold for account lockout

    @staticmethod
    def record(email, user, success, reason=None):
        """
        Record a login attempt.
        Commits the new record.
        Note: This uses the flask request object, so it must be invoked within the context of a request.
        """
        if user and success:  # on successful login, clear old logins for this user
            old = Logins.query.filter(Logins.user_id == user.id)
        else:  # otherwise, clear all old records
            old = Logins.query.filter(
                Logins.date
                < datetime.utcnow() - timedelta(seconds=Logins.time_threshold)
            )
        old.delete()

        record = Logins()  # create new record (row in the table)

        record.email = email
        record.user_id = user.id if user else None
        record.date = datetime.utcnow()  # Current UTC time
        record.success = success
        record.reason = reason

        record.ip = request.access_route[0]
        record.platform = request.user_agent.platform
        record.browser = request.user_agent.browser
        record.version = request.user_agent.version

        ldb.session.add(record)
        ldb.session.commit()  # commit new record to database

    @staticmethod
    def get_email_attempts(email):
        """Get all attempts for the same email"""
        now = datetime.utcnow()
        last = now - timedelta(seconds=Logins.time_threshold)
        return Logins.query.filter(Logins.email == email).filter(
            Logins.date.between(last, now)
        )

    @staticmethod
    def get_ip_attempts():
        """Get all attempts for the same ip (from the current request)"""
        now = datetime.utcnow()
        last = now - timedelta(seconds=Logins.time_threshold)
        return Logins.query.filter(Logins.ip == request.access_route[0]).filter(
            Logins.date.between(last, now)
        )


class Tokens(ldb.Model):
    """
    Table to hold verification tokens
    Users can have multiple verification keys options

    IMPORTANT:
    You must perform a `flask db migrate` and `flask db upgrade` to create the migration scripts
        and upgrade the local database.
    """

    __tablename__ = "verification-tokens"
    token = ldb.Column(
        UUIDType(), primary_key=True, default=uuid4
    )  # generate uuid4 when inserted
    user_id = ldb.Column(ldb.Integer, nullable=False)  # associated user ID
    expiration = ldb.Column(ldb.DateTime, nullable=False)  # expiration date

    def __repr__(self):
        return f"UserID: {self.user_id} | Token: {self.token} | Exp: {self.expiration}"

    @staticmethod
    def create_token(user):
        """
        Create a verification token for the given user.
        User must have id set (note that you need to call flush() or commit() to auto-increment a just-created user ID)
        COMMITS TO DATABASE
        """
        if user.id is None:
            logging.error(
                f"Failed to create a token for user because the user's ID isn't set): {user}"
            )
            return
        try:
            tok = Tokens()  # create new row in the verification table
            tok.user_id = user.id
            tok.expiration = datetime.utcnow() + timedelta(
                hours=24
            )  # expire in 24 hours
            tok.token = uuid4()  # set the token to a random UUID version 4
            ldb.session.add(tok)  # add to transaction
            ldb.session.commit()
            return tok
        except Exception as e:
            logging.error(
                f"Failed to create token for user: {user}. Error: {e.__class__.__name__}: {e}"
            )

    @staticmethod
    def clear_expired():
        """
        Clear all expired tokens from the tokens table
        """
        try:
            expired = Tokens.query.filter(Tokens.expiration < datetime.utcnow())
            expired.delete()  # delete all tokens
            ldb.session.commit()
        except Exception as e:
            logging.error(
                f"Failed to clear expired tokens. Error: {e.__class__.__name__}: {e}"
            )

    @staticmethod
    def delete_token(token):
        """Delete the token with the given ID"""
        Tokens.query.filter(Tokens.token == token).delete()
        ldb.session.commit()


class Searches(ldb.Model):
    """
    Table to hold verification tokens
    Users can have multiple verification keys optio

    IMPORTANT:
    When changing this model, you must change the methods SignupForm.to_user() and SignupForm.from_user().
    In addition, you must perform a `flask db migrate` and `flask db upgrade` to create the migration scripts
        and upgrade the local database.
    """

    __tablename__ = "user-searches"
    id = ldb.Column(ldb.Integer, primary_key=True)
    date = ldb.Column(ldb.DateTime, nullable=False, index=True)
    user_id = ldb.Column(
        ldb.Integer
    )  # user id that submitted this search (may not exist)

    include_concepts = ldb.Column(ldb.JSON)
    exclude_concepts = ldb.Column(ldb.JSON)
    include_relations = ldb.Column(ldb.JSON)
    exclude_relations = ldb.Column(ldb.JSON)

    representation = ldb.Column(ldb.String(30))
    authors = ldb.Column(ldb.JSON)
    journals = ldb.Column(ldb.JSON)
    grants = ldb.Column(ldb.JSON)

    start_date = ldb.Column(ldb.DateTime)
    end_date = ldb.Column(ldb.DateTime)

    limit = ldb.Column(ldb.Integer)

    def create_query(self):
        """Generate a search query dict from this search. Opposite of add_search()"""
        return {
            "include_concepts": self.include_concepts or [],
            "exclude_concepts": self.exclude_concepts or [],
            "include_relations": self.include_relations or [],
            "exclude_relations": self.exclude_relations or [],
            "representation": self.representation,
            "authors": self.authors or [],
            "journals": self.journals or [],
            "grants": self.grants or [],
            "start_date": self.start_date,
            "end_date": self.end_date,
            "limit": self.limit,
        }

    @staticmethod
    def add_search(query):
        """Given a search query in DICT form add it to the table"""
        try:
            search = Searches()
            ldb.session.add(search)
            search.user_id = current_user.id
            search.date = datetime.utcnow()

            search.include_concepts = query.get("include_concepts")
            search.exclude_concepts = query.get("exclude_concepts")
            search.include_relations = query.get("include_relations")
            search.exclude_relations = query.get("exclude_relations")
            search.representation = query.get("representation")
            search.authors = query.get("authors")
            search.journals = query.get("journals")
            search.grants = query.get("grants")
            search.start_date = query.get("start_date")
            search.end_date = query.get("end_date")
            search.limit = query.get("limit")

            ldb.session.commit()
        except Exception as e:
            logging.error(
                f"Failed to add search query to the database. Error: {e.__class__.__name__}: {e}"
            )

    @staticmethod
    def create_query_from_id(ID):
        """Given a search ID, call create_query() on that search"""
        search = Searches.query.filter_by(id=ID).first()
        return search.create_query()

    @staticmethod
    def today():
        return Searches.query.filter(
            Searches.date >= datetime.utcnow() - timedelta(days=1)
        ).order_by(Searches.date.asc())

    @staticmethod
    def this_week():
        return Searches.query.filter(
            Searches.date >= datetime.utcnow() - timedelta(days=7)
        ).order_by(Searches.date.asc())

    @staticmethod
    def this_month():
        return Searches.query.filter(
            Searches.date >= datetime.utcnow() - timedelta(days=30)
        ).order_by(Searches.date.asc())
