# flaskapp/routes/auth.py

import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
# ▼▼▼ generate_password_hash もインポートする ▼▼▼
from werkzeug.security import generate_password_hash, check_password_hash
from flaskapp.utils.db import get_db_connection

auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """ログインページの表示と認証処理"""
    if 'user_id' in session:
        return redirect(url_for('main.main_page'))

    if request.method == 'POST':
        account_id = request.form.get('username')
        password = request.form.get('password')

        if not account_id or not password:
            flash('ユーザー名とパスワードを入力してください。', 'warning')
            return render_template('login.html')

        conn = get_db_connection()
        if not conn:
            flash('データベースに接続できませんでした。', 'danger')
            return render_template('login.html')

        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT au.*, ms.shain_name 
                    FROM ms_auth_user AS au
                    LEFT JOIN ms_shainlist AS ms ON au.shain_code = ms.shain_code
                    WHERE au.account_id = %s
                """
                cursor.execute(sql, (account_id,))
                user_data = cursor.fetchone()

            # ▼▼▼【ここからパスワード判定ロジックを変更】▼▼▼
            password_ok = False
            needs_rehash = False

            # ▼▼▼【ここを修正】▼▼▼
            # ユーザーが存在し、有効で、"かつ社員に紐づいているか"を先にチェック
            if user_data and user_data['login_enabled'] and user_data['shain_code']:
                
                # 上記の条件をクリアした場合のみ、パスワードのチェックに進む
                stored_password = user_data['password_hash']
                
                # 保存されているのがハッシュ値か平文かを判定
                if stored_password and ':' in stored_password:
                    # ハッシュ値の場合
                    password_ok = check_password_hash(stored_password, password)
                else:
                    # 平文の場合
                    if stored_password == password:
                        password_ok = True
                        needs_rehash = True # 平文でのログイン成功なので、ハッシュ化が必要とマーク

            # 手順2: パスワードが正しければ、ログイン処理へ
            if password_ok:
                
                # セッションに情報を保存
                session.clear()
                session['user_id'] = user_data['user_id']
                session['shain_name'] = user_data['shain_name']
                session['role'] = user_data['role']
                
                # 手順3: 必要であれば、パスワードをハッシュ値に更新
                if needs_rehash:
                    new_hash = generate_password_hash(password)
                    with conn.cursor() as update_cursor:
                        update_cursor.execute(
                            "UPDATE ms_auth_user SET password_hash = %s WHERE user_id = %s",
                            (new_hash, user_data['user_id'])
                        )
                
                # 最終ログイン日時を更新
                if user_data['shain_code']:
                    with conn.cursor() as update_cursor:
                        update_cursor.execute(
                            "UPDATE ms_shainlist SET last_login_at = %s WHERE shain_code = %s",
                            (datetime.datetime.now(), user_data['shain_code'])
                        )
                
                conn.commit() # パスワード更新と最終ログイン日時の更新を両方確定
                
                return redirect(url_for('main.main_page'))
            
            else:
                # ログイン失敗
                flash('ユーザー名またはパスワードが違います。', 'danger')
            # ▲▲▲【変更ここまで】▲▲▲

        except Exception as e:
            flash(f'エラーが発生しました: {e}', 'danger')
        finally:
            if conn:
                conn.close()

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """ログアウト処理"""
    session.clear()
    flash('ログアウトしました。', 'info')
    return redirect(url_for('auth.login'))
