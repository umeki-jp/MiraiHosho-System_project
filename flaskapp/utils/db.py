import pymysql
from db_config import DB_CONFIG  # プロジェクトルートの設定ファイルをインポート

def get_db_connection():
    """
    データベースへの接続を取得する共通関数。
    設定は db_config.py から読み込む。
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.MySQLError as e:
        # エラーログは実際にはもっと詳細に記録することが望ましい
        print(f"データベース接続エラー: {e}")
        return None