from flask import Flask
import os
from src.config.config import Config
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# loading environment variables
load_dotenv()

app = Flask(__name__)

# calling the dev configuration
config = Config().dev_config

app.env = config.ENV

# Path for our local sql lite database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI_DEV")

# To specify to track modifications of objects and emit signals
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS")

# sql alchemy instance
db = SQLAlchemy(app)

# Flask Migrate instance to handle migrations
migrate = Migrate(app, db)

import src.routes
from src.routes import api
app.register_blueprint(api, url_prefix = "/api")

# import models to let the migrate tool know
# from src.models.user_model import User

# DevConfigDomain = "http://localhost:5000"
# TestingConfigDOMAIN = "https://mustafa27.pythonanywhere.com"
# app.config.from_object(config.ENV)

# import models to let the migrate tool know
# from src.models.user_model import User
