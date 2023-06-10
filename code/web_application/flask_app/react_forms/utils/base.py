from flask_wtf.csrf import generate_csrf
from flask import jsonify, session

########
# Base classes for creating forms with React
# Includes classes for Field and ReactForm class
########


class ReactField:
    """
    Field class

    Used to create form field allowing for front end and back end to match parameters
    """

    def __init__(self, label, name, suggest="off", required=False):
        # Field label
        self.label = label
        # Field property and object key
        self.name = name
        # Field should suggest inputs, autocomplete property
        self.suggest = suggest
        # Field placeholder
        self.placeholder = ""
        # Field default value
        self.default = ""
        # Field errors when validating
        self.errors = []
        # Determines which react component to render
        self.component = "input"
        # Field format for strings (email, text, etc.)
        self.string_format = ""
        # Field Yup type (string, number)
        self.type = ""
        # Field minimum value
        self.min = -1
        # Field maximum value
        self.max = -1
        # Field if required
        self.required = required
        # Type of HTML input (input, checkbox, dropdown)
        self.component = "input"
        # Match values with another field (give property name)
        self.ref_value_for = ""

    def validate(self, data):
        """
        Validate function
        * Validate basic form requirements, min/max value
        """
        # No data given, but not required field
        if not data and not self.required:
            return True
        # No data given
        if not data:
            self.errors.append(f"No data given for {self.name} field")
            return False
        if self.min > -1 and self.max > -1:  # If min/max is set, check if within range
            if not self.min_max(data, self.min, self.max):
                self.errors.append(f"Please make sure input is between {min} - {max}")
                return False
        return True

    def min_max(self, data, min, max):
        """
        Min max function
        * Determines if given data's length is within range
        """
        return len(data) >= min and len(data) < max

    def get_dict(self):
        """
        Get dict function
        * Returns FormikFieldTypes dictionary, so front end can genereate FormikField input
        """
        return {
            "property": self.name,
            "title": self.label,
            "type": self.string_format,  # Type for formikfield is the string format
            "required": self.required,
            "placeholder": self.placeholder,
            "component": self.component,
            "suggest": self.suggest,
            "refValueFor": self.ref_value_for,
        }


class ReactForm:
    """
    Form class
    * Used to generate groups of fields required for each form
    """

    def __init__(self):
        # User should be logged in
        self.login_required = False
        # Admin level required to use the form
        self.admin_level = 0
        # Form key renders specific object in file
        self.key = ""
        self.fields = []
        self.validators = []
        self.errors = []
        # If modifying the incoming JSON here, replace this variable
        self.edited_data = {}

    def build_form(self):
        """
        Build form function
        * Generates a Yup JSON object for front end validation and form error messages
        * Follows schema-to-yup format: https://github.com/kristianmandrup/schema-to-yup#Refs
        """

        # Yup schema requirements
        properties = {}
        required = []
        config = {"errMessages": {}}
        initial_values = {}

        # Input information for front end creation
        fields_info = []

        # Create validation schema
        for field in self.fields:

            # Add all field information (labels, format, etc)
            fields_info.append(field.get_dict())

            # Set type and format of field
            if len(field.string_format) > 0:
                properties[field.name] = {
                    "type": field.type,
                    "format": field.string_format,
                }
            if field.type == "array":
                properties[field.name] = {"type": field.type, "of": {"type": "string"}}
            else:
                properties[field.name] = {"type": field.type}

            # Set config (error messages)
            config["errMessages"][field.name] = {}

            # If required field, set error message
            if field.required:
                required.append(field.name)
                config["errMessages"][field.name] = {
                    "required": f"{field.name.capitalize()} is a required field"
                }

            # If should match other field (cannot set error msg with schema, must be overridden front end)
            if len(field.ref_value_for) > 0:
                # required.remove(field.name)
                properties[field.name].update({"refValueFor": field.ref_value_for})
                # config["errMessages"][field.name]["notOneOf"] = f"Ttest"

            # Add min/max if set & set error message
            if field.min > -1 and field.max > -1:  # error messages for min/max
                properties[field.name].update(
                    {"minLength": field.min, "maxLength": field.max}
                )
                config["errMessages"][field.name][
                    "minLength"
                ] = f"Too short! Your {field.name} must be {field.min} long"
                config["errMessages"][field.name][
                    "maxLength"
                ] = f"Too long! your ${field.name} must be under ${field.min} characters"

            if field.required and field.type == "array":
                field.min = 1
                field.max = 500
                properties[field.name].update(
                    {"minItems": field.min, "maxItems": field.max}
                )
                config["errMessages"][field.name][
                    "minItems"
                ] = f"Too short! Your {field.name} include atleast {field.min} item(s)"
                config["errMessages"][field.name][
                    "maxItems"
                ] = f"Too long! Your {field.name} must be less than {field.max} items"

            # If email format, set error message
            if field.string_format == "email":
                config["errMessages"][field.name]["format"] = "Invalid email"

            # Create and set inital values for string / number / boolean
            if field.type == "string":
                initial_values[field.name] = field.default
            if field.type == "boolean":
                initial_values[field.name] = False
            if field.type == "number":
                initial_values[field.name] = field.default
            if field.type == "array":
                initial_values[field.name] = field.default

            if field.name == "token":
                config["errMessages"].pop(field.name)
                properties.pop(field.name)

        validation_schema = {
            "title": self.key,
            "type": "object",
            "properties": properties,
            "required": required,
        }

        # TODO We either need to generate a unique CSRF token for every form request (and keep track of them separately),
        #   or make the lifetime of this global token very short (like a minute or something). First one is ideal though.
        # Generates 1 CSRF token per session
        csrf_token = session.get("csrf_token")
        if csrf_token == None:
            csrf_token = generate_csrf()
            session["csrf_token"] = csrf_token
            session.modified = True  # set the session as modified or sometimes it doesn't stick

        form_values = {
            "key": self.key,
            "validation_schema": validation_schema,
            "initial_values": initial_values,
            "config": config,
            "fields_info": fields_info,
            "csrf_token": csrf_token,
        }

        # If session's form key is found in storage, replace initial values with that
        if session.get(self.key):
            form_values["initial_values"] = session.get(self.key)

        return form_values

    def success(self):
        """
        Success function
        * Function to run when all validators have successfully passed, should be overwritten for each form
        """
        pass

    def failure(self):
        """
        Failure function
        * Returns all form errors to front end
        """
        if len(self.errors):
            return jsonify(error=self.errors[0])
        else:
            return jsonify(error="An unknown error occurred.")

    def basic_validation(self, data):
        for field in self.fields:
            if not field.validate(data[field.name]) and field.required == True:
                self.errors.extend(field.errors)
                return False
        return True

    def validate(self, data):
        """
        Validate form function
        * Initial basic form validation first
        * Custom validator functions are executed after
        """
        is_valid = True

        for validator in self.validators:
            if not validator(data):
                is_valid = False

        for field in self.fields:
            if not field.validate(data[field.name]) and field.required == True:
                self.errors.extend(field.errors)
                is_valid = False

        return is_valid
