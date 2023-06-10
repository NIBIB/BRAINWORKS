"""
Helper functions to prepare data into JSONs from forms
"""

def return_form_errors_string(errors):
    """Prepares form errors into string format for JSON"""
    str = ""
    i = 0
    for e in errors.values():
        if len(e) > 0:
            str += e[0]
            if i != len(errors.values()) - 1:
                str += ", "
        else:
            str += e.join(", ")
        i += 1
    return str


def return_dict_user(user):
    """Returns dict of user data"""
    if not user.admin:
        user.admin = 0
    return {
        "name": user.name,
        "email": user.email,
        "company": user.company,
        "department": user.department,
        "country": str(user.country),
        "purpose": user.purpose,
        "admin": user.admin,
        "verified": user.verified,
        "isLoggedIn": user.is_authenticated,
        "position": user.position,
        "id": user.id,
        "active": user.active,
    }
