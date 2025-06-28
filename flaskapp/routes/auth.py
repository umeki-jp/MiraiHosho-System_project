from flask import Blueprint, render_template, request, redirect, session

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # 今は誰でもログインできるように簡易設定
        session["user_id"] = "test_user"
        return redirect("/main")  # ログイン後、main.htmlへ
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")