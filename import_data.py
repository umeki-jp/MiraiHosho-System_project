import csv
import os
import re  # カッコを除去するために正規表現ライブラリをインポート
import pymysql
from db_config import DB_CONFIG

# --- 設定 ---
CSV_FILE = 'KEN_ALL.CSV'
TABLE_NAME = 'postal_codes'

def import_postal_data():
    """
    日本郵便の郵便番号データ（KEN_ALL.CSV）をクリーンアップして、
    データベースにインポートします。
    """
    if not os.path.exists(CSV_FILE):
        print(f"エラー: {CSV_FILE} が見つかりません。")
        return

    conn = None
    try:
        # --- 1. データベースに接続 ---
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print(f"データベース '{DB_CONFIG['db']}' に接続しました。")

        # --- 2. テーブルを一旦空にする ---
        print(f"テーブル '{TABLE_NAME}' の既存データを削除します...")
        cursor.execute(f"TRUNCATE TABLE {TABLE_NAME}")

        # --- 3. CSVを読み込み、1行ずつデータを登録 ---
        print("CSVデータのインポートを開始します...")
        sql = (
            # 重複データはエラーにせず無視する
            f"INSERT IGNORE INTO {TABLE_NAME} "
            "(postal_code, prefecture, city, town, prefecture_kana, city_kana, town_kana) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )

        record_count = 0
        with open(CSV_FILE, 'r', encoding='shift_jis') as f:
            for row in csv.reader(f):
                # CSVの各列からデータを取得
                postal_code = row[2]
                prefecture = row[6]
                city = row[7]
                town = row[8]
                prefecture_kana = row[3]
                city_kana = row[4]
                town_kana = row[5]

                # --- データ加工処理 ---
                # (1) 「以下に掲載がない場合」という町名は、空文字に変換
                if '以下に掲載がない場合' in town:
                    town = ''
                
                # (2) 町名のカッコ（〜）とその中身を削除
                # 例：「駅前町（次のビルを除く）」 -> 「駅前町」
                town = re.sub(r'（.*）', '', town)

                # (3) 「、」で区切られた町名を分割して、それぞれ別のレコードとして登録
                towns = town.split('、')
                
                for t in towns:
                    # 分割後の町名で、さらに不要なカッコが残っていれば削除
                    # カナの町名も同様に処理しますが、分割は漢字の町名に合わせます
                    processed_town = re.sub(r'\(.*\)', '', t).strip()
                    
                    # カナの処理はシンプルに（分割は考慮しない）
                    processed_town_kana = re.sub(r'\(.*\)', '', town_kana).strip()

                    data_to_insert = (
                        postal_code, prefecture, city, processed_town,
                        prefecture_kana, city_kana, processed_town_kana
                    )
                    cursor.execute(sql, data_to_insert)
                    
                    # 実際に登録された件数のみカウント
                    if cursor.rowcount > 0:
                        record_count += 1
        
        # --- 4. 変更をデータベースに反映 ---
        conn.commit()
        print(f"インポート完了。{record_count}件のレコードを登録しました。")

    except pymysql.MySQLError as e:
        print(f"データベースエラーが発生しました: {e}")
        if conn:
            conn.rollback()  # エラー時は変更を元に戻す

    finally:
        # --- 5. 接続を閉じる ---
        if conn:
            conn.close()
            print("MySQLとの接続を閉じました。")

if __name__ == '__main__':
    import_postal_data()