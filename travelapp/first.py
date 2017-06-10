from flask import Flask, request, render_template, url_for, redirect
import os
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, PasswordField, validators
from wtforms.fields.html5 import URLField, EmailField
from . import config as cfg
from . import dbutil 
import json
from datetime import datetime, date

USER_ID = 8
USERNAME = "bdaves"

app = Flask(__name__)
app.secret_key = "Development Key"

def jsonDefault(obj):
    if isinstance(obj, (datetime, date)):
        serial = obj.isoformat()
        return serial

    return json.dumps(obj, default=jsonDefault)

@app.route('/')
def index():
    conn = dbutil.connect()
    cursor = conn.cursor()
    location_data = dbutil.get_locations(cursor, USERNAME)
    return render_template('maps.html', APIKEY=cfg.GOOGLE_MAPS_API, location_data=json.dumps(location_data, default=jsonDefault))


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

@app.route('/newLocation', methods=['GET', 'POST'])
def addLocation():
    form = LocationForm()
    if form.validate_on_submit():
        title = form.title.data
        lat = form.latitude.data
        lng = form.longitude.data
        arrivalDate = form.arrivalDate.data
        departureDate = form.departureDate.data
        url = form.website.data
        conn = dbutil.connect()
        cursor = conn.cursor()
        dbutil.insert_location(cursor, USER_ID, title, lat, lng, arrivalDate, departureDate, url)
        return redirect(url_for('index'))
    return render_template('newLocation.html', form=form)

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
def addUser():
    form = UserForm()
    if form.validate_on_submit():
        firstname = form.firstname.data
        lastname = form.lastname.data
        username = form.username.data
        password = form.password.data
        email = form.email.data
        conn = dbutil.connect()
        cursor = conn.cursor()
        dbutil.insert_user(cursor, username, firstname, lastname, email, password)
        return redirect(url_for('index'))
    return render_template('newUser.html', form=form)
