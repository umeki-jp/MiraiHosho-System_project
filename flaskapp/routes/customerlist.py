# ==============================================================================
# 必要なライブラリをインポートします
# ==============================================================================
from flask import Blueprint, render_template, request, redirect, url_for, flash
import pymysql
import datetime
import json # 申請データをJSON形式で保存するためにインポート

# 外部ファイルから、フォームで扱うフィールド名のリストを読み込みます
from flaskapp.utils.ms01_customerlist_fields import field_names 
from flaskapp.utils import dropdown_options 

# このファイル（customerlist.py）を 'customerlist_bp' という名前でBlueprintとして登録します
customerlist_bp = Blueprint("customerlist", __name__)

STATUS_MAP = {
    0: "未登録",
    1: "登録済",
    # 以下は今後の拡張用
    # 2: "承認待",
    # 3: "差し戻し",
    # 4: "確定",
    # 5: "削除済"
}
# ==============================================================================
# ヘルパー関数
# ==============================================================================
def get_db_connection():
    """データベース接続を取得します"""
    return pymysql.connect(
        host="localhost", user="root", password="mirai",
        db="miraihosho_system", charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def get_approvers(conn):
    """承認権限を持つ社員のリストを取得します"""
    with conn.cursor() as cursor:
        # ms_shainlist と ms_auth_user を結合して、権限が'管理者'または'社員A'の社員を取得
        sql = """
            SELECT s.shain_code, s.shain_name
            FROM ms_shainlist s
            JOIN ms_auth_user a ON s.shain_code = a.user_id
            WHERE a.role IN ('管理者', '社員A')
            ORDER BY s.shain_code
        """
        cursor.execute(sql)
        return cursor.fetchall()

def get_field_labels():
    """日本語の項目名リストを返します"""
    return {
        "customer_code": "顧客コード", "name": "名前", "name_kana": "フリガナ", "typeofcustomer": "区分",
        "individual_nationality": "個人_国籍", "individual_birthDate": "個人_生年月日", "individual_age": "個人_年齢", "individual_gender": "個人_性別",
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
@customerlist_bp.route("/masters/customerlist")
def show_customerlist():
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
    
    page_str = request.args.get("page", "1")
    page = int(page_str) if page_str.isdigit() else 1
    
    limit_str = request.args.get("limit", "20")
    limit = int(limit_str) if limit_str.isdigit() else 20

    offset = (page - 1) * limit

    conn = get_db_connection()
    results = []
    total = 0

    try:
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

        with conn.cursor() as cursor:
            count_sql = f"SELECT COUNT(*) as total FROM ms01_customerlist WHERE {where_sql}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total'] or 0
            
            params_with_limit = params.copy()
            params_with_limit['limit'] = limit
            params_with_limit['offset'] = offset
            
            sql = f"SELECT * FROM ms01_customerlist WHERE {where_sql} ORDER BY customer_code DESC LIMIT %(limit)s OFFSET %(offset)s"
            cursor.execute(sql, params_with_limit)
            results = cursor.fetchall()

        date_fields_to_format = ["individual_birthDate", "corporate_foundationdate", "registration_date", "update_date"]
        for customer in results:
            # ステータスを数値に変換 (この処理を追加)
            if customer.get('registration_status') is not None and str(customer.get('registration_status')).isdigit():
                customer['registration_status'] = int(customer['registration_status'])
            else:
                customer['registration_status'] = None # 数値でない場合はNoneにして「不明」と表示させる

            # 日付のフォーマット (既存の処理)
            for field in date_fields_to_format:
                if customer.get(field) and isinstance(customer.get(field), (datetime.date, datetime.datetime)):
                    customer[field] = customer[field].strftime('%Y-%m-%d')
            
            # Noneを空文字に変換 (既存の処理)
            for key, value in customer.items():
                if value is None:
                    customer[key] = ''
    finally:
        if conn.open:
            conn.close()
            
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
        status_map=STATUS_MAP  # この行を追加
    )

# ==============================================================================
# 新規顧客の登録・登録申請機能
# ==============================================================================
@customerlist_bp.route("/masters/customer/new", methods=["GET", "POST"])
def customer_new():
    conn = get_db_connection()
    try:
        button_config = {"show_instant_register": True, "show_approval_register": True}

        if request.method == "POST":
            action = request.form.get("action")
            form_data = {f: request.form.get(f, "").strip() for f in field_names}
            
            # ▼▼▼ 修正 ▼▼▼ (ここから日付妥当性チェックを追加)
            birth_date_str = form_data.get("individual_birthDate")
            if birth_date_str: # 日付が入力されている場合のみチェック
                try:
                    # YYYYMMDD形式の文字列を日付に変換しようと試みる
                    datetime.datetime.strptime(birth_date_str, '%Y%m%d')
                except ValueError:
                    # 変換に失敗した場合（=ありえない日付の場合）
                    flash("個人_生年月日に入力された日付が正しくありません。(例: 19800230)", "error")
                    # エラーメッセージをセットし、元のフォーム画面に戻す
                    return render_template(
                        "masters/customer_form.html", 
                        form_data=form_data, 
                        mode="create", 
                        page_title="新規 顧客登録", 
                        button_config=button_config,
                        status_map=STATUS_MAP # この行を追加
                    )

            if not form_data.get("name"):
                flash("名前を入力してください。", "error")
                return render_template(
                    "masters/customer_form.html", 
                    form_data=form_data, 
                    mode="create", 
                    page_title="新規 顧客登録", 
                    button_config=button_config,
                    status_map=STATUS_MAP # この行を追加
                )

            if action == "request_new_approval":
                approvers = get_approvers(conn)
                field_labels = get_field_labels()
                changes = [{"label": field_labels.get(k, k), "before": "", "after": v} for k, v in form_data.items() if v]
                return render_template(
                    "shared/update_confirm.html", 
                    changes=changes, form_data=form_data, submit_url=url_for('customerlist.customer_new'),
                    is_approval_flow=True, approvers=approvers, final_action_value="submit_new_approval"
                )
            
            elif action == "submit_new_approval":
                approver_id = request.form.get('approver_id')
                with conn.cursor() as cursor:
                    requester_id = 'admin' # 仮
                    sql = """
                        INSERT INTO ts51_approval_requests (target_table, target_id, request_type, request_data, requester_id, approver_id, status)
                        VALUES (%s, %s, %s, %s, %s, %s, '申請中')
                    """
                    request_data_json = json.dumps(form_data, ensure_ascii=False)
                    cursor.execute(sql, ('ms01_customerlist', 'NEW', '新規', request_data_json, requester_id, approver_id))
                    conn.commit()
                flash(f"新規顧客の登録を申請しました。", "success")
                return redirect(url_for("customerlist.show_customerlist"))

            elif action == "register_instant":
                with conn.cursor() as cursor:
                    cursor.execute("SELECT MAX(CAST(SUBSTRING(customer_code, 2) AS UNSIGNED)) AS max_num FROM ms01_customerlist WHERE customer_code LIKE 'C%'")
                    max_num = cursor.fetchone()['max_num']
                    new_number = (max_num or 0) + 1
                    customer_code = f"C{new_number:07d}"

                    datetime_fields = ["individual_birthDate", "corporate_foundationdate", "registration_date", "update_date"]
                    integer_fields = ["individual_age"]
                    form_data = {f: request.form.get(f, "").strip() for f in field_names}
                    values = [customer_code]
                    for f in field_names:
                        val = form_data.get(f, "")
                        if (f in datetime_fields or f in integer_fields) and val == "":
                            values.append(None)
                        else:
                            values.append(val)
                            
                    # ステータスとして「1: 登録済」を追加
                    values.append(1) 

                    # SQLの組み立てと実行
                    column_names = ", ".join(["customer_code"] + field_names + ["registration_status"])
                    placeholders = ", ".join(["%s"] * len(values))
                    sql = f"INSERT INTO ms01_customerlist ({column_names}) VALUES ({placeholders})"
                    
                    cursor.execute(sql, values)
                    conn.commit()
                flash(f"顧客コード {customer_code} が発行されました。", "success")
                return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))

        # GETリクエスト（画面の初期表示）の場合
        form_data = {f: "" for f in field_names}
        
        # ステータスに「未登録」を意味する `0` を設定
        form_data['registration_status'] = 0 
        
        return render_template(
            "masters/customer_form.html", 
            form_data=form_data, 
            mode="create", 
            page_title="新規 顧客登録", 
            button_config=button_config,
            status_map=STATUS_MAP # テンプレートで使えるようにstatus_mapを渡す
        )
        
    finally:
        if conn.open:
            conn.close()

# ==============================================================================
# 既存顧客の編集・更新・削除・承認申請機能
# ==============================================================================
@customerlist_bp.route("/masters/customer/<customer_code>", methods=["GET", "POST"])
def customer_edit(customer_code):
    conn = get_db_connection()
    try:
        if request.method == "POST":
            action = request.form.get("action")
            
            if action in ["update_instant", "request_update_approval"]:
                form_data = {f: request.form.get(f, "").strip() for f in field_names}
                
                # ▼▼▼ 修正 ▼▼▼ (ここから日付妥当性チェックを追加)
                birth_date_str = form_data.get("individual_birthDate")
                if birth_date_str: # 日付が入力されている場合のみチェック
                    try:
                        datetime.datetime.strptime(birth_date_str, '%Y%m%d')
                    except ValueError:
                        flash("個人_生年月日に入力された日付が正しくありません。(例: 19800230)", "error")
                        # 編集モードで元のフォーム画面に戻す
                        button_config = {"show_instant_update": True, "show_approval_update": True, "show_instant_delete": True, "show_approval_delete": True}
                        return render_template("masters/customer_form.html", form_data=form_data, mode="edit", button_config=button_config)
                # ▲▲▲ 修正 ▲▲▲ (チェックここまで)
                
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM ms01_customerlist WHERE customer_code = %s", (customer_code,))
                    before_data = cursor.fetchone()

                if not before_data:
                    flash("更新対象の顧客データが見つかりません。", "error")
                    return redirect(url_for('customerlist.show_customerlist'))

                # ▼▼▼ 修正 ▼▼▼ (スクリーンショットの問題を解決するための新しい比較ロジック)
                changes = []
                field_labels = get_field_labels()
                date_field_keys = ["individual_birthDate", "corporate_foundationdate", "registration_date", "update_date"]

                for field in field_names:
                    before_val = before_data.get(field) # 元の値 (日付オブジェクトなど)
                    after_val = form_data.get(field)   # フォームからの値 (文字列)

                    # --- ステップ1: 比較のために値を正規化 ---
                    # 比較を正確に行うため、両方の値を同じ「YYYY-MM-DD」形式の文字列に揃える
                    before_normalized = ""
                    if isinstance(before_val, (datetime.date, datetime.datetime)):
                        before_normalized = before_val.strftime('%Y-%m-%d')
                    elif before_val is not None:
                        before_normalized = str(before_val)

                    after_normalized = ""
                    if after_val:
                        try:
                            if field in ['individual_birthDate', 'corporate_foundationdate']:
                                # 8桁数字ならYYYYMMDDとして扱う
                                if len(after_val) == 8 and after_val.isdigit():
                                    after_normalized = datetime.datetime.strptime(after_val, '%Y%m%d').strftime('%Y-%m-%d')
                                elif '-' in after_val:
                                    after_normalized = after_val
                                else:
                                    after_normalized = after_val
                            elif field in date_field_keys:
                                after_normalized = after_val
                            else:
                                after_normalized = after_val
                        except (ValueError, TypeError):
                            after_normalized = after_val # 解析失敗時は元の文字列のまま

                    # --- ステップ2: 正規化した値で比較を実行 ---
                    if before_normalized != after_normalized:
                        # --- ステップ3: 変更がある場合のみ、表示用の値を作成 ---
                        # 表示の際は、ユーザーの入力形式に合わせる
                        before_display = ""
                        if isinstance(before_val, (datetime.date, datetime.datetime)):
                            # 生年月日は、表示も「YYYYMMDD」形式に統一する
                            if field == 'individual_birthDate':
                                before_display = before_val.strftime('%Y%m%d')
                            else:
                                before_display = before_val.strftime('%Y-%m-%d')
                        elif before_val is not None:
                            before_display = str(before_val)

                        changes.append({
                            "label": field_labels.get(field, field),
                            "before": before_display,
                            "after": after_val if after_val is not None else ""
                        })
                # ▲▲▲ 修正 ▲▲▲ (新しい比較ロジックここまで)       changes.append({"label": field_labels.get(field, field), "before": before_value, "after": after_value})
                
                if not changes:
                    flash("変更された項目がありません。", "info")
                    return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))

                is_approval_flow = (action == "request_update_approval")
                approvers = get_approvers(conn) if is_approval_flow else None
                final_action_value = "submit_update_approval" if is_approval_flow else "submit_update_instant"
                return render_template("shared/update_confirm.html", changes=changes, form_data=form_data, submit_url=url_for('customerlist.customer_edit', customer_code=customer_code), approvers=approvers, is_approval_flow=is_approval_flow, final_action_value=final_action_value)

            elif action == "submit_update_instant":
                form_data = {f: request.form.get(f, "").strip() for f in field_names}
                with conn.cursor() as cursor:
                    datetime_fields = ["individual_birthDate", "corporate_foundationdate", "registration_date", "update_date"]
                    integer_fields = ["individual_age"]
                    values = []
                    for f in field_names:
                        val = form_data.get(f, "")
                        if (f in datetime_fields or f in integer_fields) and val == "":
                            values.append(None)
                        else:
                            values.append(val)

                # 各項目のUPDATE文を生成
                    update_clause = ", ".join(f"{col} = %s" for col in field_names)
                    
                    # ステータスを更新する処理を追加
                    update_clause += ", registration_status = %s"
                    values.append(1) # 値として「1: 登録済」を追加
                    
                    # WHERE句のための顧客コードを追加
                    values.append(customer_code)

                    sql = f"UPDATE ms01_customerlist SET {update_clause} WHERE customer_code = %s"
                    cursor.execute(sql, values)
                    conn.commit()
                return render_template("shared/action_done.html", action_label="更新")
            # ▲▲▲【ここまで修正】▲▲▲

            elif action == "submit_update_approval":
                form_data = {f: request.form.get(f, "").strip() for f in field_names}
                approver_id = request.form.get('approver_id')
                with conn.cursor() as cursor:
                    requester_id = 'admin' # 仮
                    sql_request = """
                        INSERT INTO ts51_approval_requests (target_table, target_id, request_type, request_data, requester_id, approver_id, status)
                        VALUES (%s, %s, %s, %s, %s, %s, '申請中')
                    """
                    request_data_json = json.dumps(form_data, ensure_ascii=False)
                    cursor.execute(sql_request, ('ms01_customerlist', customer_code, '更新', request_data_json, requester_id, approver_id))
                    cursor.execute("UPDATE ms01_customerlist SET registration_status = '更新承認待ち' WHERE customer_code = %s", (customer_code,))
                    conn.commit()
                flash("顧客情報の更新を申請しました。", "success")
                return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))

            elif action in ["delete_instant", "request_delete_approval"]:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT application_number FROM tr01_applicationlist WHERE customer_code = %s", (customer_code,))
                    related_applications = cursor.fetchall()
                if related_applications:
                    deletable = False
                    app_numbers = ", ".join([app['application_number'] for app in related_applications])
                    message = f"この顧客（{customer_code}）は申込番号 ({app_numbers}) と紐づいているため、削除できません。"
                else:
                    deletable = True
                    message = f"本当に「{customer_code}」を削除しますか？"
                
                is_approval_flow = (action == "request_delete_approval")
                approvers = get_approvers(conn) if is_approval_flow and deletable else None
                final_action_value = "submit_delete_approval" if is_approval_flow else "submit_delete_instant"
                return render_template("shared/delete_confirm.html", message=message, deletable=deletable, submit_url=url_for('customerlist.customer_delete_confirmed', customer_code=customer_code), approvers=approvers, is_approval_flow=is_approval_flow, final_action_value=final_action_value)

        button_config = {"show_instant_update": True, "show_approval_update": True, "show_instant_delete": True, "show_approval_delete": True}
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ms01_customerlist WHERE customer_code = %s", (customer_code,))
            customer = cursor.fetchone()
        if not customer:
            flash("指定された顧客が見つかりませんでした。", "error")
            return redirect(url_for("customerlist.show_customerlist"))
        
        # ▼▼▼【ここに追加】ステータスを数値型に変換 ▼▼▼
        if customer.get('registration_status') is not None:
            customer['registration_status'] = int(customer['registration_status'])

        # ▼▼▼ 修正 ▼▼▼ (ここから日付の表示形式を修正)
        date_fields_to_format = ["individual_birthDate", "corporate_foundationdate", "registration_date", "update_date"]
        for field in date_fields_to_format:
            if customer.get(field) and isinstance(customer.get(field), (datetime.date, datetime.datetime)):
                # 生年月日・設立年月日はYYYYMMDD形式、それ以外はYYYY-MM-DD形式でフォーマット
                if field in ["individual_birthDate", "corporate_foundationdate"]:
                    customer[field] = customer[field].strftime('%Y%m%d')
                else:
                    customer[field] = customer[field].strftime('%Y-%m-%d')
            # 追加: 文字列でYYYY-MM-DD形式の場合もYYYYMMDDに変換
            elif field in ["individual_birthDate", "corporate_foundationdate"] and isinstance(customer.get(field), str) and '-' in customer.get(field):
                customer[field] = customer[field].replace('-', '')
        # ▲▲▲ 修正 ▲▲▲ (日付の表示形式の修正ここまで)

        for key, value in customer.items():
            if value is None:
                customer[key] = ''
        # テンプレートに status_map を渡す
        return render_template(
            "masters/customer_form.html", 
            form_data=customer, 
            mode="edit", 
            button_config=button_config,
            status_map=STATUS_MAP # この行を追加
        )    

    finally:
        if conn.open:
            conn.close()

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
                requester_id = 'admin' # 仮
                sql_request = """
                    INSERT INTO ts51_approval_requests (target_table, target_id, request_type, request_data, requester_id, approver_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s, '申請中')
                """
                cursor.execute(sql_request, ('ms01_customerlist', customer_code, '削除', None, requester_id, approver_id))
                cursor.execute("UPDATE ms01_customerlist SET registration_status = '削除承認待ち' WHERE customer_code = %s", (customer_code,))
                conn.commit()
            # ここで完了画面
            return render_template("shared/action_done.html", action_label="削除申請")
        
        elif action == "submit_delete_instant":
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM ms01_customerlist WHERE customer_code = %s", (customer_code,))
                conn.commit()
            # ここで完了画面
            return render_template("shared/action_done.html", action_label="削除")
    except Exception as e:
        flash(f"処理中にエラーが発生しました: {e}", "error")
    finally:
        if conn.open:
            conn.close()
    
    # どちらでもない場合は一覧に戻す
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

