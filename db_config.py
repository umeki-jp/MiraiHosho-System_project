# db_config.py

import pymysql
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',      # データベースのユーザー名
    'password': 'mirai',  # データベースのパスワード
    'db': 'miraihosho_system', # データベース名
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor # 結果を辞書形式で取得
}