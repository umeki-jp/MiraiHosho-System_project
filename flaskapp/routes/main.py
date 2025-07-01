# main.py に貼り付ける完成版コード

from flask import Blueprint, render_template, session, redirect, url_for
from flaskapp.utils.db import get_db_connection

main_bp = Blueprint("main", __name__)

@main_bp.route("/main")
def main_page():
    # ログインしていない場合はログインページへリダイレクト
    if 'account_id' not in session:
        return redirect(url_for('auth.login'))

    # テンプレートに渡す変数をあらかじめ定義
    data = None
    error_message = None
    conn = None

    try:
        # conn = get_db_connection() # 将来ここでDB接続
        # if not conn:
        #     raise Exception("データベース接続に失敗しました。")
        
        # --- 将来、ここにダッシュボード用のデータを取得する処理を追加 ---
        # with conn.cursor() as cursor:
        #     cursor.execute("SELECT ...")
        #     data = cursor.fetchall()
        pass # 現状はデータベース処理がないため、何もせず通過

    except Exception as e:
        # DB接続やデータ取得でエラーが発生した場合の処理
        print(f"データベースエラー (main_page): {e}")
        error_message = "ダッシュボード情報の読み込みに失敗しました。管理者にお問い合わせください。"
        data = None # データは無い状態にする
    
    finally:
        # 接続があれば必ず閉じる
        if conn:
            conn.close()
            
    # テンプレートに変数を渡す
    # (shain_nameはbase.htmlでセッションから直接読み込まれるため、ここで渡す必要はありません)
    return render_template("main.html", data=data, error_message=error_message)