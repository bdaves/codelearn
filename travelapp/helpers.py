
from flask import render_template
import uuid
import dns.resolver

from . import dbutil
from . import email


def send_user_validation_email(cursor, user_guid):
    user = dbutil.get_user_by_guid(cursor, user_guid)

    if not user:
        print("Requested user does not exist:", user_guid)
        return

    email_address = user.get('email', None)
    if not email_address:
        print("User does not have an email address: ", user_guid)
        return

    token = uuid.uuid1().hex
    dbutil.set_verification_token(cursor, user_guid, token)

    travel_site = {'name': 'Travel Together', 'team_name': 'Travel Lovers'}
    email_message = render_template('welcome_email.txt', travel_site=travel_site, token=token)

    print("Email sent")
    email.send_email(email_address, "Welcome", email_message)


def is_valid_email_server(user_email):
    if not user_email:
        return False

    email_parts = user_email.split('@')

    if len(email_parts) != 2:
        return False

    email_server = email_parts[1]

    try:
        results = list(dns.resolver.query(email_server, 'MX'))
        return len(results) > 0
    except dns.resolver.NXDOMAIN:
        return False
