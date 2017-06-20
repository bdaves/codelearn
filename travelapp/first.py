from flask import Flask, request, render_template, url_for, redirect, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, PasswordField, SelectField, HiddenField, validators
from wtforms.fields.html5 import URLField, EmailField
from . import config as cfg
from . import dbutil 
import json
from datetime import datetime, date

from .decorators import logged_in, with_cursor

USER_ID = 1
USERNAME = "bdaves"

app = Flask(__name__)
app.secret_key = "Development Key"

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
    form = LoginForm()
    if form.validate_on_submit():
        username = session['username'] = request.form['username']
        password = request.form['password']
        if dbutil.validate_user(cursor, username, password):
            return redirect(url_for('index'))
        else:
            # TODO: Need to mark that username/password did not agree
            pass

    return render_template('login.html', form=form)

@app.route('/')
@logged_in
@with_cursor
def index(cursor):
    username = session['username']
    trips = dbutil.get_trips(cursor, username)
    return render_template('trips.html', trips=trips)


def sortLocations(order, locations):
    newLocations = dict()

    for idx, location_guid in enumerate(order):
        newLocations[location_guid] = idx

    result = [None] * len(order)

    for location in locations:
        if location['guid'] in newLocations:
            result[newLocations[location['guid']]] = location
        else:
            result.append(location)

    return [location for location in result if location]




@app.route('/trip/<guid>')
@logged_in
@with_cursor
def trip(guid, cursor):
    location_data = dbutil.get_locations(cursor, guid)
    trip = dbutil.get_trip(cursor, guid)

    if not trip:
        return redirect(url_for('index'))

    if trip['order']:
        location_data = sortLocations(trip['order'], location_data)

    return render_template(
        'maps.html',
        APIKEY=cfg.GOOGLE_MAPS_API,
        location_data=json.dumps(location_data, default=jsonDefault),
        locations=location_data,
        trip=trip)


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
        arrivalDate = form.arrivalDate.data
        departureDate = form.departureDate.data
        url = form.website.data
        trip_guid = form.trip_guid.data
        if (trip_guid == guid):
            dbutil.insert_location(cursor, trip_guid, title, lat, lng, arrivalDate, departureDate, url)
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


@app.route('/reorderLocations/<trip_guid>', methods=['GET', 'POST'])
@logged_in
@with_cursor
def reorderLocations(trip_guid, cursor):
    locations = request.form.getlist("locations[]")
    dbutil.insert_order(cursor, trip_guid, locations)

    return redirect(url_for('index'))


@app.route('/newLocation2/<guid>', methods=['GET', 'POST'])
@with_cursor
@logged_in
def addLocation2(guid, cursor):
    form = LocationForm(request.values, trip_guid=guid)
    if form.validate_on_submit():
        title = form.title.data
        lat = form.latitude.data
        lng = form.longitude.data
        arrivalDate = form.arrivalDate.data
        departureDate = form.departureDate.data
        url = form.website.data
        trip_guid = form.trip_guid.data
        if (trip_guid == guid):
            dbutil.insert_location(cursor, trip_guid, title, lat, lng, arrivalDate, departureDate, url)
            return redirect(url_for('trip', guid=trip_guid))
        else:
            flash("invalid location for this trip")

    return render_template('newLocation2.html', form=form, APIKEY=cfg.GOOGLE_MAPS_API)

class UserForm(FlaskForm):
    firstname = StringField('First Name', 
        [validators.InputRequired('  *Please input your first name'), validators.Length(max=64)])
    lastname = StringField('Last Name', 
        [validators.InputRequired('  *Please input your last name'), validators.Length(max=64)])
    username = StringField('Username', 
        [validators.InputRequired('  *Please select a username'), validators.Length(max=64)])
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

        return redirect(url_for('index'))

    return render_template('newGroup.html', form=form)


class TripForm(FlaskForm):
    title = StringField('Trip Title', 
        [validators.InputRequired('  *Please input a trip title'), validators.Length(max=128)])
    group = SelectField('Group', coerce=str)

    def set_groups(self, groups):
        self.group.choices = groups


@app.route('/newTrip', methods=['GET', 'POST'])
@logged_in
@with_cursor
def addTrip(cursor):
    form = TripForm(request.form)
    username = session['username']
    groups = dbutil.get_groups(cursor, username)
    choices = [(group['guid'], group['name']) for group in groups]
    form.set_groups(choices)

    if form.validate_on_submit():
        title = form.title.data
        group = form.group.data
        trip_guid = dbutil.insert_trip(cursor, group, title)
        return redirect(url_for('trip', guid=trip_guid))

    return render_template('newTrip.html', form=form)


@app.route('/deleteTrip/<guid>', methods=['GET'])
@logged_in
@with_cursor
def deleteTrip(guid, cursor):
    dbutil.delete_trip(cursor, guid)

    return redirect(url_for('index'))



@app.route('/logout')
@logged_in
def logout():
    session.pop('username')
    return redirect(url_for('login'))
