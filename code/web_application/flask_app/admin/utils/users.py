from flask_app.models import Users, UserArchive
from sqlalchemy import func


def user_charts():
    """Create plot layout for Users admin page"""

    # User countries
    countries = (
        Users.query.with_entities(Users.country, func.count())
        .group_by(Users.country)
        .all()
    )
    user_countries = []
    for tup in countries:
        user_countries.append({"name": str(tup[0]), "value": tup[1]})

    # User positions
    positions = (
        Users.query.with_entities(Users.position, func.count())
        .group_by(Users.position)
        .all()
    )
    user_positions = []
    for tup in positions:
        user_positions.append({"name": tup[0], "value": tup[1]})

    # User status
    total = Users.query.count()
    active = Users.query.filter(Users.active == True)  # all active accounts
    verified = active.filter(
        Users.verified == True
    ).count()  # active accounts with verified email
    unverified = active.count() - verified  # active accounts with unverified email
    inactive = total - active.count()  # inactive accounts
    deleted = UserArchive.query.count()  # deleted users

    user_status = [
        {"name": "Verified", "value": verified},
        {"name": "Unverified", "value": unverified},
        {"name": "Banned", "value": inactive},
        {"name": "Deleted", "value": deleted},
    ]

    # User creation
    # Count occurrences of users at that specific date with dictionary
    user_creation_dict = {}
    users = Users.query.order_by(Users.created.asc())
    total = 0
    for user in users:
        total += 1
        date_string = f"{user.created.year}-{user.created.month}-{user.created.day}"
        user_creation_dict.update({date_string: total})
    # Create list of user date
    dates = []
    for key in user_creation_dict:
        dates.append(key)

    # Add user dates in sorted order
    user_creation = []
    for date in dates:
        user_creation.append({"name": date, "value": user_creation_dict.get(date)})

    return {
        "countries": user_countries,
        "positions": user_positions,
        "status": user_status,
        "total": str(total),
        "created": user_creation,
    }
