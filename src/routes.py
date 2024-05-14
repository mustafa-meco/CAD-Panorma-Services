from flask import render_template, request, jsonify
from src.lib.CADUtils import *
import datetime
from src import app, config
from flask import Blueprint
from flask_cors import CORS

# main blueprint to be registered with application
api = Blueprint('api', __name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')



from src.cad_routes import *

