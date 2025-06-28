from flask import Blueprint, render_template, session

main_bp = Blueprint("main", __name__)

@main_bp.route("/main")
def main_page():
    user = session.get("user_id", "ゲスト")
    return render_template("main.html", user_id=user)