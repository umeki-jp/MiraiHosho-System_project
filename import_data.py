import csv
import os
import mysql.connector
from mysql.connector import errorcode

# --- MySQL接続設定 ---
# ご自身の環境に合わせて設定を変更してください
DB_CONFIG = {
    'user': 'root', 
    'password': 'mirai',
    'host': '127.0.0.1', 
    'database': 'miraihosho_system'
}

# --- その他設定 ---
CSV_FILE = 'KEN_ALL.CSV'
TABLE_NAME = 'postal_codes'

def import_data_to_mysql():
    if not os.path.exists(CSV_FILE):
        print(f"エラー: {CSV_FILE} が見つかりません。")
        return

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print(f"データベース '{DB_CONFIG['database']}' に接続しました。")

        print(f"テーブル '{TABLE_NAME}' の既存データを削除します...")
        cursor.execute(f"TRUNCATE TABLE {TABLE_NAME}")
        print("データ削除完了。")

        print("CSVデータのインポートを開始します...")
        count = 0
        # INSERT IGNOREは、万が一他の原因で重複が発生した場合も処理を止めないため、念のため残しておきます。
        sql_insert = (
            f"INSERT IGNORE INTO {TABLE_NAME} "
            "(postal_code, prefecture, city, town, prefecture_kana, city_kana, town_kana) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )

        with open(CSV_FILE, 'r', encoding='shift_jis') as f:
            reader = csv.reader(f)
            for row in reader:
                postal_code = row[2]
                prefecture_kana = row[3]
                city_kana = row[4]
                town_kana = row[5]
                prefecture = row[6]
                city = row[7]
                town = row[8]
                
                if town == '以下に掲載がない場合':
                    town, town_kana = '', ''
                
                # 「、」で町名が分割されているケースには対応
                towns = town.split('、')
                towns_kana = town_kana.split('、')

                for i, t in enumerate(towns):
                    t_kana = towns_kana[i] if i < len(towns_kana) else ''
                    
                    # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
                    # (かっこ)やその中身を削除する処理をなくし、元のデータをそのまま使用します。
                    # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
                    
                    data = (postal_code, prefecture, city, t, prefecture_kana, city_kana, t_kana)
                    cursor.execute(sql_insert, data)
                    
                    if cursor.rowcount > 0:
                        count += 1
        
        conn.commit()
        print(f"インポートが完了しました。{count}件のレコードを登録しました。")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("ユーザー名またはパスワードが間違っています。")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"データベース '{DB_CONFIG['database']}' が存在しません。")
        else:
            print(err)
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("MySQLとの接続を閉じました。")

if __name__ == '__main__':
    import_data_to_mysql()