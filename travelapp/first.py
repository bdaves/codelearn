from flask import Flask, request, render_template, url_for, redirect
import os
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, validators
from wtforms.fields.html5 import URLField
app = Flask(__name__)
app.secret_key = "Development Key"

@app.route('/')
def index():
    apikey = os.getenv('GOOGLE_MAPS_API')
    return render_template('maps.html', APIKEY=apikey)


class LocationForm(FlaskForm):
    title = StringField('Location Name', 
        [validators.InputRequired('Please input a location'), validators.Length(max=128)])
    latitude = DecimalField('Latitude', 
        [validators.InputRequired('Please input the latitude of the location')], places=4)
    longitude = DecimalField('Longitude', 
        [validators.InputRequired('Please input the longitude of the location')], places=4)
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
        return redirect(url_for('index'))
    return render_template('newLocation.html', form=form)

