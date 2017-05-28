from flask import Flask, request, render_template
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
    title = StringField('Location Name')
    latitude = DecimalField('Latitude')
    longitude = DecimalField('Longitude')
    arrivalDate = DateField('Arrival Date')
    departureDate = DateField('Departure Date')
    website = URLField('Location Website URL')
    # title = StringField('Location Name', 
    #     [validators.InputRequired('Please input a location'), validators.Length(max=128)])
    # latitude = DecimalField('Latitude', 
    #     [validators.InputRequired('Please input the latitude of the location')], places=4)
    # longitude = DecimalField('Longitude', 
    #     [validators.InputRequired('Please input the longitude of the location')], places=4)
    # arrivalDate = DateField('Arrival Date')
    # departureDate = DateField('Departure Date')
    # website = URLField('Location Website URL')

@app.route('/newLocation', methods=['GET', 'POST'])
def addLocation():
    print(dir(request))
    form = LocationForm()
    print(form.validate())
    print("valid", form.validate_on_submit())
    if form.validate_on_submit():
        title = form.title
        lat = form.latitude
        lng = form.longitude
        arrivalDate = form.arrivalDate
        departureDate = form.departureDate
        url = form.website
        print("title: ", title, type(title))
        print("latitude: ", lat, type(lat))
        print("longitude: ", lng, type(lng))
        print("arrival Date: ", arrivalDate, type(arrivalDate))
        print("departure Date: ", departureDate, type(departureDate))
        print("url: ", url, type(url))
    print("title: ", form.title.errors)
    print("latitude: ", form.latitude.errors)
    print("longitude: ", form.longitude.errors)
    print("arrival Date: ", form.arrivalDate.errors)
    print("departure Date: ", form.departureDate.errors)
    print("url: ", form.website.errors)
    return render_template('newLocation.html', form=form)

