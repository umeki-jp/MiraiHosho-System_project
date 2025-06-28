from flask import Flask
from flaskapp.routes.main import main_bp
from flaskapp.routes.auth import auth_bp
from flaskapp.routes.applications import applications_bp
from flaskapp.routes.root import root_bp
from flaskapp.routes.customerlist import customerlist_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = "your-secret-key"  
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(root_bp)
    app.register_blueprint(customerlist_bp)


    return app