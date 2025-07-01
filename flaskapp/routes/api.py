# flaskapp/routes/api.py

from flask import Blueprint, jsonify, request
import pymysql  # ### 変更点 1: エラー処理のためにインポート
from flaskapp.utils.db import get_db_connection # ### 変更点 2: 共通関数をインポート

# 'api'という名前のブループリントを作成
api_bp = Blueprint('api', __name__, url_prefix='/api')

# ### 変更点 3: ファイル内のDB接続設定を削除 ###
# --- MySQL接続設定 ---
# DB_CONFIG = { ... }  <- このブロックを丸ごと削除


@api_bp.route('/search_address_by_postal')
def search_address_by_postal():
    """郵便番号から住所を検索するAPI（ハイフンあり・なし両対応）"""
    postal_code_from_form = request.args.get('postal_code', '')
    postal_code_for_db = postal_code_from_form.replace('-', '')

    if not postal_code_for_db.isdigit() or len(postal_code_for_db) != 7:
        return jsonify({'error': '無効な郵便番号形式です'}), 400

    # ### 変更点 4: 共通の接続関数を呼び出すように変更 ###
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'データベースに接続できません'}), 500

    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM postal_codes WHERE postal_code = %s"
            cursor.execute(query, (postal_code_for_db,))
            results = cursor.fetchall()
            return jsonify(results)
            
    except pymysql.MySQLError as err: # ### 変更点 5: エラーの種類を pymysql に合わせる
        return jsonify({'error': f'データベースエラー: {err}'}), 500
    finally:
        if conn:
            conn.close()


@api_bp.route('/search_postal_by_address')
def search_postal_by_address():
    """住所から郵便番号を検索するAPI"""
    prefecture = request.args.get('prefecture', '')
    city = request.args.get('city', '')
    town = request.args.get('town', '')

    if not prefecture and not city and not town:
        return jsonify({'error': '少なくとも一つの検索条件を指定してください'}), 400

    # ### 変更点 4: 共通の接続関数を呼び出すように変更 ###
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'データベースに接続できません'}), 500

    try:
        with conn.cursor() as cursor:
            query_parts = []
            params = []

            if prefecture:
                query_parts.append("prefecture = %s")
                params.append(prefecture)
            if city:
                query_parts.append("city LIKE %s")
                params.append(f"%{city}%")
            if town:
                query_parts.append("town LIKE %s")
                params.append(f"%{town}%")

            base_query = "SELECT * FROM postal_codes WHERE "
            full_query = base_query + " AND ".join(query_parts) + " LIMIT 100"
            cursor.execute(full_query, tuple(params))
            results = cursor.fetchall()
            return jsonify(results)
    except pymysql.MySQLError as err: # ### 変更点 5: エラーの種類を pymysql に合わせる
        return jsonify({'error': f'データベースエラー: {err}'}), 500
    finally:
        if conn:
            conn.close()