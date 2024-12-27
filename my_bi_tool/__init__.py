# my_bi_tool/__init__.py
from flask import Flask
from config import Config
from .extensions import mysql
from .routes.auth import auth_bp
from .routes.main import main_bp
from .routes.data import data_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize MySQL extension
    mysql.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(data_bp, url_prefix='/data')

    return app

