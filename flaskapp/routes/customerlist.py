import datetime
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flaskapp.utils.db import get_db_connection
from flaskapp.utils.ms01_customerlist_fields import field_names 
from flaskapp.common import constants

customerlist_bp = Blueprint("customerlist", __name__)


# ==============================================================================
# ヘルパー関数
# ==============================================================================
def json_serial(obj):
    """日時オブジェクトをJSONで扱える形式(ISOフォーマット)に変換する"""
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def get_approvers(conn):
    """承認権限を持つ社員のリストを取得します"""
    with conn.cursor() as cursor:
        # ms_shainlist と ms_auth_user を結合して、権限が'管理者'または'社員A'の社員を取得
        sql = """
            SELECT s.shain_code, s.shain_name
            FROM ms_shainlist s
            JOIN ms_auth_user a ON s.shain_code = a.shain_code
            WHERE a.role IN (1,2,3,4,5)  -- マスター、管理者A、管理者B、管理者C、社員A
            ORDER BY s.shain_code
        """
        cursor.execute(sql)
        return cursor.fetchall()

def get_field_labels():
    """日本語の項目名リストを返します"""
    return {
        "customer_code": "顧客コード", "name": "名前", "name_kana": "フリガナ", "typeofcustomer": "区分",
        "individual_nationality": "個人_国籍", "individual_birthdate": "個人_生年月日", "individual_age": "個人_年齢", "individual_gender": "個人_性別",
        "individual_postalcode": "個人_郵便番号", "individual_prefecture": "個人_都道府県", "individual_city": "個人_市区町村", "individual_address": "個人_番地", "individual_currentaddresscategory": "個人_現住所区分",
        "individual_tel1": "個人_TEL1", "individual_tel2": "個人_TEL2", "individual_mail": "個人_Mail", "individual_workplace": "個人_勤務先",
        "individual_workplace_postalcode": "個人_勤務先_郵便番号", "individual_workplace_prefecture": "個人_勤務先_都道府県",
        "individual_workplace_city": "個人_勤務先_市区町村", "individual_workplace_address": "個人_勤務先_番地", "individual_workplace_tel": "個人_勤務先_TEL",
        "individual_occupation": "個人_職種", "individual_industry": "個人_業種", "corporate_registrationnumber": "法人_会社法人等番号",
        "corporate_representative": "法人_代表者", "corporate_postalcode": "法人_郵便番号", "corporate_prefecture": "法人_都道府県",
        "corporate_city": "法人_市区町村", "corporate_address": "法人_番地", "corporate_foundationdate": "法人_設立年月日",
        "corporate_capital": "法人_資本金", "corporate_tel1": "法人_TEL1", "corporate_tel2": "法人_TEL2",
        "corporate_mail": "法人_Mail", "corporate_businesscontent": "法人_事業内容", "customer_rank": "ランク",
        "customer_rankdetails": "ランク詳細", "customer_remarks": "備考", "registration_date": "登録日",
        "registration_shain": "登録者", "update_date": "更新日", "update_shain": "更新者", "registration_status": "登録状況"
    }

# ==============================================================================
# 顧客情報の一覧表示・検索機能
# ==============================================================================
# customerlist.py の中の関数をこれに置き換え

@customerlist_bp.route("/masters/customerlist")
def show_customerlist():
    # 検索フィルターの値を取得
    filters = {
        "customer_code": request.args.get("customer_code", "").strip(),
        "name": request.args.get("name", "").strip(),
        "name_kana": request.args.get("name_kana", "").strip(),
        "tel": request.args.get("tel", "").strip(),
        "workplace": request.args.get("workplace", "").strip(),
        "registration_status": request.args.get("registration_status", "").strip(),
        "registration_date_from": request.args.get("registration_date_from", "").strip(),
        "registration_date_to": request.args.get("registration_date_to", "").strip(),
    }
    has_search = any(filters.values())
    
    # ページネーションの設定
    page_str = request.args.get("page", "1")
    page = int(page_str) if page_str.isdigit() else 1
    
    limit_str = request.args.get("limit", "20")
    limit = int(limit_str) if limit_str.isdigit() else 20

    offset = (page - 1) * limit

    # データベース接続
    conn = get_db_connection()

    # ★★★ 接続失敗時のチェック ★★★
    if not conn:
        flash("データベースに接続できませんでした。管理者にお問い合わせください。", "danger")
        return render_template(
            "masters/customerlist.html", customers=[], total=0, page=1, limit=limit, 
            total_pages=0, filters=filters, has_search=has_search, 
            selected_limit=str(limit), registration_status=constants.registration_status_MAP
        )

    results = []
    total = 0
    try:
        # 検索条件の組み立て
        where_clauses = ["1=1"]
        params = {}

        if filters["customer_code"]:
            where_clauses.append("customer_code LIKE %(customer_code)s")
            params['customer_code'] = f"%{filters['customer_code']}%"
        if filters["name"]:
            where_clauses.append("name LIKE %(name)s")
            params['name'] = f"%{filters['name']}%"
        if filters["name_kana"]:
            where_clauses.append("name_kana LIKE %(name_kana)s")
            params['name_kana'] = f"%{filters['name_kana']}%"
        if filters["tel"]:
            where_clauses.append("(individual_tel1 LIKE %(tel)s OR individual_tel2 LIKE %(tel)s OR corporate_tel1 LIKE %(tel)s OR corporate_tel2 LIKE %(tel)s)")
            params['tel'] = f"%{filters['tel']}%"
        if filters["workplace"]:
            where_clauses.append("individual_workplace LIKE %(workplace)s")
            params['workplace'] = f"%{filters['workplace']}%"
        if filters["registration_status"]:
            where_clauses.append("registration_status = %(registration_status)s")
            params['registration_status'] = filters['registration_status']
        if filters["registration_date_from"]:
            where_clauses.append("registration_date >= %(registration_date_from)s")
            params['registration_date_from'] = filters['registration_date_from']
        if filters["registration_date_to"]:
            where_clauses.append("registration_date <= %(registration_date_to)s")
            params['registration_date_to'] = filters['registration_date_to']

        where_sql = " AND ".join(where_clauses)

        # データベース操作
        with conn.cursor() as cursor:
            # 総件数を取得
            count_sql = f"SELECT COUNT(*) as total FROM ms01_customerlist WHERE {where_sql}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total'] or 0
            
            # 表示するデータを取得
            params_with_limit = params.copy()
            params_with_limit['limit'] = limit
            params_with_limit['offset'] = offset
            
            sql = f"SELECT * FROM ms01_customerlist WHERE {where_sql} ORDER BY customer_code DESC LIMIT %(limit)s OFFSET %(offset)s"
            cursor.execute(sql, params_with_limit)
            results = cursor.fetchall()

    except Exception as e:
        flash(f"データの取得中にエラーが発生しました: {e}", "danger")
        total = 0
        results = []
    finally:
        if conn:
            conn.close()
            
    # テンプレートに渡す値を計算
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    return render_template(
        "masters/customerlist.html",
        customers=results, 
        total=total, 
        page=page, 
        limit=limit, 
        total_pages=total_pages,
        filters=filters, 
        has_search=has_search, 
        selected_limit=str(limit),
        registration_status=constants.registration_status_MAP
    )

# ==============================================================================
# 新規顧客の登録・登録申請機能
# ==============================================================================
@customerlist_bp.route("/masters/customer/new", methods=["GET", "POST"])
def customer_new():
    """新規顧客の登録（承認なし）"""
    conn = get_db_connection()
    try:
        button_config = {"show_instant_register": True}
        
        if request.method == "POST":
            form_data = {f: request.form.get(f, "").strip() for f in field_names}
            
            # --- 1. 共通の入力チェック ---
            if not form_data.get("name"):
                flash("名前を入力してください。", "error")
                return render_template("masters/customer_form.html", mode="create", form_data=form_data, button_config=button_config)

            date_fields_to_check = ["individual_birthdate", "corporate_foundationdate"]
            for field in date_fields_to_check:
                date_str = form_data.get(field)
                if date_str:
                    try:
                        datetime.datetime.strptime(date_str, '%Y%m%d')
                    except ValueError:
                        flash(f"入力された日付（{get_field_labels().get(field)}）が正しくありません。(例: 20250131)", "error")
                        return render_template("masters/customer_form.html", mode="create", form_data=form_data, button_config=button_config)

            # --- 2. データベース登録処理 ---
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(CAST(SUBSTRING(customer_code, 2) AS UNSIGNED)) AS max_num FROM ms01_customerlist WHERE customer_code LIKE 'C%'")
                max_num = cursor.fetchone()['max_num']
                customer_code = f"C{(max_num or 0) + 1:07d}"

                # ▼▼▼【ここから修正】▼▼▼
                # 郵便番号を「NNN-NNNN」形式に強制フォーマット
                for field in ['individual_postalcode', 'individual_workplace_postalcode', 'corporate_postalcode']:
                    code = form_data.get(field)
                    if code:
                        digits = code.replace('-', '')
                        if len(digits) == 7 and digits.isdigit():
                            form_data[field] = f"{digits[:3]}-{digits[3:]}"
                
                # サーバー側で値を設定
                form_data['registration_shain'] = session.get('shain_name', '不明なユーザー')
                form_data['registration_date'] = datetime.datetime.now()
                form_data['registration_status'] = 1

                # データベース保存用に値を準備
                values = [customer_code]
                datetime_fields = ["individual_birthdate", "corporate_foundationdate", "registration_date", "update_date"]
                integer_fields = ["individual_age"]
                for f in field_names:
                    val = form_data.get(f, "")
                    if (f in datetime_fields or f in integer_fields) and val == "":
                        values.append(None)
                    else:
                        values.append(val)
                # ▲▲▲【修正ここまで】▲▲▲
                
                column_names = ", ".join(["customer_code"] + field_names)
                sql_insert = f"INSERT INTO ms01_customerlist ({column_names}) VALUES ({', '.join(['%s']*len(values))})"
                cursor.execute(sql_insert, values)
                conn.commit()

            flash(f"顧客コード {customer_code} を発行し、登録しました。", "success")
            return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))
        
        # --- [GET] 新規登録ページを最初に表示する時の処理 ---
        return render_template("masters/customer_form.html", mode="create", form_data={f: "" for f in field_names}, button_config=button_config)
    
    finally:
        if conn: conn.close()

# ==============================================================================
# 顧客の削除・削除申請の実行機能
# ==============================================================================
@customerlist_bp.route("/masters/customer/<customer_code>", methods=["GET", "POST"])
def customer_edit(customer_code):
    """顧客の編集・更新・削除（承認なし）"""
    conn = get_db_connection()
    try:
        # --- [POST] 「更新」または「削除」ボタンが押された時の処理 ---
        if request.method == "POST":
            action = request.form.get("action")

            # ###【更新】処理 ###
            if action == "update_instant":
                form_data = {f: request.form.get(f, "").strip() for f in field_names}
                with conn.cursor() as cursor:
                    update_parts, values = [], []
                    for f in field_names:
                        # 更新対象のフィールドのみをリストアップ
                        if f not in ["registration_date", "registration_shain", "update_date", "update_shain", "registration_status"]:
                            update_parts.append(f"{f} = %s")
                            values.append(form_data.get(f))
                    
                    update_parts.extend(["update_date = %s", "update_shain = %s"])
                    values.extend([datetime.datetime.now(), session.get('shain_name', '不明なユーザー'), customer_code])
                    
                    sql = f"UPDATE ms01_customerlist SET {', '.join(update_parts)} WHERE customer_code = %s"
                    cursor.execute(sql, values)
                    conn.commit()
                flash(f"顧客コード（{customer_code}）の情報を更新しました。", "success")
                return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))
            
            # ###【削除】処理 ###
            elif action == "delete_instant":
                # (この後のステップで、削除確認画面のロジックをここに追加します)
                pass
        
        # --- [GET] 編集ページを最初に表示する時の処理 ---
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ms01_customerlist WHERE customer_code = %s", (customer_code,))
            customer = cursor.fetchone()
        
        if not customer:
            flash("指定された顧客が見つかりませんでした。", "error")
            return redirect(url_for("customerlist.show_customerlist"))
        
        # --- 表示するボタンを決定 ---
        button_config = {}
        user_role = session.get('role', 0)
        # グループA, B (社員A) の場合
        if user_role in [1, 3]:
            button_config = {"show_instant_update": True, "show_instant_delete": True}
        # グループB (社員B) の場合
        elif user_role == 4:
            button_config = {"show_instant_update": True, "show_instant_delete": False} # 削除は不可
        
        return render_template(
            "masters/customer_form.html", 
            mode="edit", 
            form_data=customer,
            button_config=button_config
        )
    finally:
        if conn: conn.close()
        
# ==============================================================================
# 顧客の削除・削除申請の実行機能
# ==============================================================================
@customerlist_bp.route("/masters/customer/delete/<customer_code>", methods=["POST"])
def customer_delete_confirmed(customer_code):
    conn = get_db_connection()
    try:
        action = request.form.get("action")
        
        if action == "submit_delete_approval":
            approver_id = request.form.get('approver_id')
            with conn.cursor() as cursor:
                requester_id = session.get('shain_code', 'UNKNOWN')
                
                # 申請レコードを登録
                sql_request = "INSERT INTO ts51_approval_requests (target_table, target_id, request_type, requester_id, approver_id, status) VALUES (%s, %s, %s, %s, %s, 0)"
                cursor.execute(sql_request, ('ms01_customerlist', customer_code, '削除', requester_id, approver_id))
                
                # 顧客のステータスを「2: 承認待ち」に変更
                cursor.execute("UPDATE ms01_customerlist SET registration_status = 2 WHERE customer_code = %s", (customer_code,))
                conn.commit()
            
            flash(f"顧客（{customer_code}）の削除を申請しました。", "success")
            return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))
        
        elif action == "submit_delete_instant":
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM ms01_customerlist WHERE customer_code = %s", (customer_code,))
                conn.commit()
            flash(f"顧客（{customer_code}）を削除しました。", "success")
            return redirect(url_for('customerlist.show_customerlist'))

    except Exception as e:
        flash(f"処理中にエラーが発生しました: {e}", "error")
    finally:
        if conn: conn.close()
    
    return redirect(url_for('customerlist.show_customerlist'))

# ==============================================================================
# 完了画面表示用のルート
# ==============================================================================
@customerlist_bp.route("/masters/customer/done")
def customer_done():
    action_label = request.args.get("action_label", "操作")
    return render_template("shared/action_done.html", action_label=action_label)

# ==============================================================================
# エラーページ表示用のルート
# ==============================================================================
@customerlist_bp.route("/masters/customer/error")
def customer_error():
    error_message = request.args.get("error_message", "不明なエラーが発生しました。")
    return render_template("shared/error.html", error_message=error_message)