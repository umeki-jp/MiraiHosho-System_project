# main.py

from flask import Blueprint, render_template, session, redirect, url_for

main_bp = Blueprint("main", __name__)

@main_bp.route("/main")
def main_page():
    if 'account_id' not in session:
        return redirect(url_for('auth.login'))
        
    # shain_name を渡す処理がなくても、共通処理のおかげで表示される
    return render_template("main.html")
        
    # ▼▼▼【ここを修正】▼▼▼
    # セッションからアカウントIDと社員名を取得
    account_id = session.get("account_id", "ゲスト")
    shain_name = session.get("shain_name", "ゲスト") # 社員名を取得

    # テンプレートに両方の情報を渡す
    return render_template("main.html", account_id=account_id, shain_name=shain_name)
    # ▲▲▲【修正ここまで】▲▲▲