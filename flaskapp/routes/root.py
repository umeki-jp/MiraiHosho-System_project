from flask import Blueprint, redirect

root_bp = Blueprint("root", __name__)

@root_bp.route("/")
def index():
    return redirect("/login")