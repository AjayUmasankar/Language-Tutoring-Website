from flask import Flask
from flask_login import LoginManager
from extention import db
import config

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config.from_object(config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
