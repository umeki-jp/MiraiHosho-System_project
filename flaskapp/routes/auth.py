# flaskapp/routes/auth.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flaskapp.utils.db import get_db_connection # ### 変更点 1: 共通関数をインポート

auth_bp = Blueprint("auth", __name__)

# ### 変更点 2: ファイル内のDB接続関数を削除 ###
# def get_db_connection(): ... <- この関数を丸ごと削除


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        account_id = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        if not conn:
            flash("データベースに接続できませんでした。", "danger")
            return render_template("login.html")

        try:
            with conn.cursor() as cursor:
                # ▼▼▼【ここを修正】▼▼▼
                sql = """
                    SELECT
                        a.user_id, a.account_id, a.password_hash, a.role, a.shain_code,
                        s.shain_name
                    FROM
                        ms_auth_user a
                    LEFT JOIN
                        ms_shainlist s ON a.shain_code = s.shain_code
                    WHERE
                        a.account_id = %s AND a.login_enabled = 1
                """
                # ▲▲▲【a.shain_code -> a.shain_code など、すべて小文字に修正】▲▲▲

                cursor.execute(sql, (account_id,))
                user = cursor.fetchone()

                

                if user and user['password_hash'] == password:
                    session.clear()
                    session['user_id'] = user['user_id']
                    session['account_id'] = user['account_id']
                    session['role'] = int(user['role'])
                    session['shain_code'] = user['shain_code']
                    session['shain_name'] = user['shain_name']
                    
                    return redirect(url_for("main.main_page"))
                else:
                    flash("ユーザー名またはパスワードが間違っています。", "danger")

        except Exception as e:
            flash(f"認証中にエラーが発生しました: {e}", "danger")
        finally:
            if conn:
                conn.close()

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("ログアウトしました。", "info")
    return redirect(url_for("auth.login"))