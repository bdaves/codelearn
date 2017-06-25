from flask import Flask, request, render_template, url_for, redirect, session, flash, jsonify, Markup
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, PasswordField, SelectField, HiddenField, validators
from wtforms.fields.html5 import URLField, EmailField
from . import config as cfg
from . import dbutil
from . import helpers
import json
from datetime import datetime, date

from .decorators import logged_in, with_cursor

app = Flask(__name__)
app.secret_key = "Development Key"


def has_permissions(cursor, group_guid, permissions):
    username = session['username']
    return dbutil.has_permissions(cursor, username, group_guid, permissions)


def jsonDefault(obj):
    if isinstance(obj, (datetime, date)):
        serial = obj.isoformat()
        return serial

    return json.dumps(obj, default=jsonDefault)


class LoginForm(FlaskForm):
    username = StringField('Username',
                           [validators.InputRequired('  *Please enter your username'), validators.Length(max=64)])
    password = PasswordField('Password',
                             [validators.InputRequired('  *Please enter your password'), validators.Length(max=64)])


@app.route('/login', methods=['GET', 'POST'])
@with_cursor
def login(cursor):
    if 'username' in session:
        session.clear()

    form = LoginForm()
    if form.validate_on_submit():
        username = request.form['username']
        password = request.form['password']
        (validation_state, user_guid) = dbutil.validate_user(cursor, username, password)
        print("after check", validation_state, user_guid)
        if validation_state is None:
            flash(Markup("""Before attempting to login, please look at your email for an account validation request.

            If you do not have the validation email, <a href="{0}">click here</a> to request a new validation email.""".
                         format(url_for("request_validation", user_guid=user_guid))), "message")
            print("Doing nothing")
        elif validation_state:
            # Validated and username/password match
            session['username'] = username
            dbutil.user_logged_in(cursor, username)

            return redirect(url_for('index'))
        else:
            flash("Either the username is unknown, or the password did not match.  Please retry.", "error")

    return render_template('login.html', form=form)


@app.route("/newValidation/<user_guid>")
@with_cursor
def request_validation(user_guid, cursor):
    helpers.send_user_validation_email(cursor, user_guid)
    flash("Please check your email for your validation link.  Select link in email to validate", "message")
    return redirect(url_for("login"))


@app.route('/')
@logged_in
@with_cursor
def index(cursor):
    username = session['username']
    trips = dbutil.get_trips(cursor, username)
    return render_template('trips.html', trips=trips)


@app.route('/groups')
@logged_in
@with_cursor
def groups(cursor):
    username = session['username']
    user_groups = dbutil.get_groups(cursor, username)
    return render_template('groups.html', groups=user_groups)


@app.route('/group/<guid>')
@logged_in
@with_cursor
def group(guid, cursor):
    members = dbutil.get_members(cursor, guid)
    return render_template('group.html', members=members, guid=guid)


def sortLocations(order, locations):
    new_locations = dict()

    for idx, location_guid in enumerate(order):
        new_locations[location_guid] = idx

    result = [None] * len(order)

    for location in locations:
        if location['guid'] in new_locations:
            result[new_locations[location['guid']]] = location
        else:
            result.append(location)

    return [location for location in result if location]


@app.route('/trip/<guid>')
@logged_in
@with_cursor
def trip(guid, cursor):
    location_data = dbutil.get_locations(cursor, guid)
    user_trip = dbutil.get_trip(cursor, guid)

    if not user_trip:
        return redirect(url_for('index'))

    if user_trip['order']:
        location_data = sortLocations(user_trip['order'], location_data)

    return render_template(
        'maps.html',
        APIKEY=cfg.GOOGLE_MAPS_API,
        GOOGLE_PLACE_API=cfg.GOOGLE_PLACE_API,
        location_data=json.dumps(location_data, default=jsonDefault),
        locations=location_data,
        trip=user_trip)


class LocationForm(FlaskForm):
    title = StringField('Location Name',
                        [validators.InputRequired('  *Please input a location'), validators.Length(max=128)])
    latitude = DecimalField('Latitude',
                            [validators.InputRequired('  *Please input the latitude of the location')], places=4)
    longitude = DecimalField('Longitude',
                             [validators.InputRequired('  *Please input the longitude of the location')], places=4)
    arrivalDate = DateField('Arrival Date', [validators.optional()])
    departureDate = DateField('Departure Date', [validators.optional()])
    website = URLField('Location Website URL')
    trip_guid = HiddenField('Trip Guid')


@app.route('/newLocation/<guid>', methods=['GET', 'POST'])
@with_cursor
@logged_in
def addLocation(guid, cursor):
    form = LocationForm(request.values, trip_guid=guid)
    if form.validate_on_submit():
        title = form.title.data
        lat = form.latitude.data
        lng = form.longitude.data
        arrival_date = form.arrivalDate.data
        departure_date = form.departureDate.data
        url = form.website.data
        trip_guid = form.trip_guid.data
        if trip_guid == guid:
            dbutil.insert_location(cursor, trip_guid, title, lat, lng, arrival_date, departure_date, url)
            return redirect(url_for('trip', guid=trip_guid))
        else:
            flash("invalid location for this trip")

    return render_template('newLocation.html', form=form, GOOGLE_PLACE_API=cfg.GOOGLE_PLACE_API)


@app.route('/deleteLocation/<trip_guid>/<location_guid>', methods=['GET'])
@logged_in
@with_cursor
def deleteLocation(trip_guid, location_guid, cursor):
    dbutil.delete_location(cursor, trip_guid, location_guid)

    return redirect(url_for('trip', guid=trip_guid))


@app.route('/reorderLocations/<trip_guid>', methods=['POST'])
@logged_in
@with_cursor
def reorderLocations(trip_guid, cursor):
    locations = request.form.getlist("locations[]")
    dbutil.insert_order(cursor, trip_guid, locations)

    return "", 200


@app.route('/newShortLocation/<trip_guid>', methods=['GET', 'POST'])
@logged_in
@with_cursor
def addShortLocation(trip_guid, cursor):
    location = request.form.getlist("location[]")

    guid = dbutil.insert_short_location(cursor, trip_guid, location[0], location[1], location[2])

    return jsonify(guid=guid), 200


@app.route('/newLocation2/<guid>', methods=['GET', 'POST'])
@with_cursor
@logged_in
def addLocation2(guid, cursor):
    form = LocationForm(request.values, trip_guid=guid)
    if form.validate_on_submit():
        title = form.title.data
        lat = form.latitude.data
        lng = form.longitude.data
        arrival_date = form.arrivalDate.data
        departure_date = form.departureDate.data
        url = form.website.data
        trip_guid = form.trip_guid.data

        if trip_guid == guid:
            dbutil.insert_location(cursor, trip_guid, title, lat, lng, arrival_date, departure_date, url)
            return redirect(url_for('trip', guid=trip_guid))
        else:
            flash("invalid location for this trip")

    return render_template('newLocation2.html', form=form, APIKEY=cfg.GOOGLE_MAPS_API)


class UserForm(FlaskForm):
    firstname = StringField('First Name',
                            [validators.InputRequired('  *Please input your first name'),
                             validators.Length(max=64)])
    lastname = StringField('Last Name',
                           [validators.InputRequired('  *Please input your last name'),
                            validators.Length(max=64)])
    username = StringField('Username',
                           [validators.InputRequired('  *Please select a username'),
                            validators.Length(max=64)])
    password = PasswordField('Password',
                             [validators.InputRequired('  *Please input a password'),
                              validators.EqualTo('confirmpwd', message='  *Passwords must match'),
                              validators.Length(max=64)])
    confirmpwd = PasswordField('Confirm Password',
                               [validators.InputRequired('  *Please confirm your password'),
                                validators.Length(max=64)])
    email = EmailField('Email', [validators.EqualTo('confirmemail', message='  *Emails must match'),
                                 validators.InputRequired('  *Please input your email')])
    confirmemail = EmailField('Confirm Email', [validators.InputRequired('  *Please confirm your email')])


@app.route('/newUser', methods=['GET', 'POST'])
@with_cursor
def addUser(cursor):
    form = UserForm()
    if form.validate_on_submit():
        firstname = form.firstname.data
        lastname = form.lastname.data
        username = form.username.data
        password = form.password.data
        email = form.email.data

        dbutil.insert_user(cursor, username, firstname, lastname, email, password)

        return redirect(url_for('index'))
    return render_template('newUser.html', form=form)


class GroupForm(FlaskForm):
    name = StringField('Group Name',
                       [validators.InputRequired('  *Please create a group name'), validators.Length(max=128)])


class AddToGroupForm(FlaskForm):
    group = SelectField('Group', coerce=str)
    names = StringField('usernames / email addresses',
                        [validators.InputRequired('  *Please create a group name'), validators.Length(max=128)])
    permission = SelectField('Permission Level', coerce=int)

    def set_groups(self, user_groups):
        self.group.choices = user_groups

    def set_permissions(self, permissions):
        self.permission.choices = permissions


class AddToGroupForm2(FlaskForm):
    names = StringField('usernames / email addresses',
                        [validators.InputRequired('  *Please create a group name'), validators.Length(max=128)])
    permission = SelectField('Permission Level', coerce=int)

    def set_permissions(self, permissions):
        self.permission.choices = permissions


@app.route('/newGroup', methods=['GET', 'POST'])
@logged_in
@with_cursor
def addGroup(cursor):
    form = GroupForm()
    if form.validate_on_submit():
        name = form.name.data
        guid = dbutil.insert_group(cursor, name)
        username = session['username']

        dbutil.insert_group_member(cursor, guid, username, "OWNER")

        return redirect(url_for('groups'))

    return render_template('newGroup.html', form=form)


def display_groups(form, cursor):
    username = session['username']
    user_groups = dbutil.get_groups(cursor, username)
    choices = [(user_group['guid'], user_group['name']) for user_group in user_groups]
    form.set_groups(choices)


def display_permissions(form, cursor):
    permissions = dbutil.get_permissions(cursor)
    choices = [(permission['permission_id'], permission['name']) for permission in permissions]
    form.set_permissions(choices)


def parseNames(names):
    emails = []
    usernames = []
    namelist = [name.strip() for name in names.split(',')]
    for name in namelist:
        if "@" in name:
            emails.append(name)
        else:
            usernames.append(name)

    return {"emails": emails, "usernames": usernames}


@app.route('/addToGroup', methods=['GET', 'POST'])
@logged_in
@with_cursor
def addToGroup(cursor):
    form = AddToGroupForm()
    display_groups(form, cursor)
    display_permissions(form, cursor)
    if form.validate_on_submit():
        user_group = form.group.data
        names = form.names.data
        permissions = dbutil.get_permissions_list(cursor, "can_modify_group")
        if has_permissions(cursor, user_group, permissions):
            permission = form.permission.data
            names = parseNames(names)
            print(names["emails"])
            print(names["usernames"])
            print(permission)
            print(user_group)
            dbutil.add_to_group(cursor, user_group, names["emails"], names["usernames"], permission)

            return redirect(url_for('index'))

        else:
            flash("you must be an owner or admin to add people to a group")

    return render_template('addToGroup.html', form=form)


@app.route('/addToGroup2/<guid>', methods=['GET', 'POST'])
@logged_in
@with_cursor
def addToGroup2(guid, cursor):
    form = AddToGroupForm2()
    display_permissions(form, cursor)
    if form.validate_on_submit():
        names = form.names.data
        permissions = dbutil.get_permissions_list(cursor, "can_modify_group")
        if has_permissions(cursor, guid, permissions):
            permission = form.permission.data
            names = parseNames(names)
            dbutil.add_to_group(cursor, guid, names["emails"], names["usernames"], permission)

            return redirect(url_for('group', guid=guid))

        else:
            flash("you must be an owner or admin to add people to a group")

    return render_template('addToGroup2.html', form=form, guid=guid)


class TripForm(FlaskForm):
    title = StringField('Trip Title',
                        [validators.InputRequired('  *Please input a trip title'), validators.Length(max=128)])
    group = SelectField('Group', coerce=str)

    def set_groups(self, user_groups):
        self.group.choices = user_groups


@app.route('/newTrip', methods=['GET', 'POST'])
@logged_in
@with_cursor
def addTrip(cursor):
    form = TripForm(request.form)
    display_groups(form, cursor)
    if form.validate_on_submit():
        title = form.title.data
        user_group = form.group.data
        trip_guid = dbutil.insert_trip(cursor, user_group, title)
        return redirect(url_for('trip', guid=trip_guid))

    return render_template('newTrip.html', form=form)


@app.route('/deleteTrip/<guid>', methods=['GET'])
@logged_in
@with_cursor
def deleteTrip(guid, cursor):
    dbutil.delete_trip(cursor, guid)

    return redirect(url_for('index'))


@app.route('/deleteGroup/<guid>', methods=['GET'])
@logged_in
@with_cursor
def deleteGroup(guid, cursor):
    dbutil.delete_group(cursor, guid)

    return redirect(url_for('groups'))


@app.route('/logout')
def logout():
    session.clear()

    return redirect(url_for('login'))


@app.route('/verify/<token>', methods=['GET', 'POST'])
@with_cursor
def verification(token, cursor):
    # Logout if somehow this browser has a logged in user
    if 'username' in session:
        session.clear()

    form = LoginForm()
    if form.validate_on_submit():
        username = request.form['username']
        password = request.form['password']
        (login_valid, guid) = dbutil.validate_user(cursor, username, password, token)
        if login_valid:
            session['username'] = username
            flash("Your account is now verified.  Welcome!")
            dbutil.user_is_verified(cursor, username)
            return redirect(url_for('index'))
        else:
            flash("Either the entered username is unknown, or the password did not match.  Please retry.")

    return render_template('verify.html', form=form, token=token)
