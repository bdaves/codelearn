from flask import Flask, request, render_template
import os

app = Flask(__name__)

@app.route('/')
def index():
    apikey = os.getenv('GOOGLE_MAPS_API')
    return render_template('maps.html', APIKEY=apikey)
