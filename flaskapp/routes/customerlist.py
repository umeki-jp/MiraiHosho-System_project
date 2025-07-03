# ==============================================================================
# 必要なライブラリをインポートします
# ==============================================================================
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import datetime
import json # 申請データをJSON形式で保存するためにインポート

from flaskapp.utils.db import get_db_connection
# 外部ファイルから、フォームで扱うフィールド名のリストを読み込みます
from flaskapp.utils.ms01_customerlist_fields import field_names 
from flaskapp.utils import dropdown_options 
from flaskapp.common import constants

# このファイル（customerlist.py）を 'customerlist_bp' という名前でBlueprintとして登録します
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
    conn = get_db_connection()
    try:
        # --- [POST] フォームのボタンが押された時の処理 ---
        if request.method == "POST":
            action = request.form.get("action")
            form_data = {f: request.form.get(f, "").strip() for f in field_names}
            
            # ###【即時登録】の場合 ###
            if action == "register_instant":
                # 必須項目チェック
                if not form_data.get("name"):
                    flash("名前を入力してください。", "error")
                    approvers = get_approvers(conn)
                    button_config = {"show_instant_register": True, "show_approval_register": True}
                    return render_template("masters/customer_form.html", form_data=form_data, mode="create", page_title="新規 顧客登録", button_config=button_config, approvers=approvers)

                with conn.cursor() as cursor:
                    cursor.execute("SELECT MAX(CAST(SUBSTRING(customer_code, 2) AS UNSIGNED)) AS max_num FROM ms01_customerlist WHERE customer_code LIKE 'C%'")
                    max_num = cursor.fetchone()['max_num']
                    customer_code = f"C{(max_num or 0) + 1:07d}"

                    form_data['registration_shain'] = session.get('shain_name', '不明なユーザー')
                    form_data['registration_date'] = datetime.datetime.now()
                    form_data['registration_status'] = 1 # 1: 登録済

                    datetime_fields = ["individual_birthDate", "corporate_foundationdate", "registration_date", "update_date"]
                    integer_fields = ["individual_age"]
                    values = [customer_code]
                    for f in field_names:
                        val = form_data.get(f, "")
                        values.append(None if (f in datetime_fields or f in integer_fields) and val == "" else val)
                    
                    column_names = ", ".join(["customer_code"] + field_names)
                    placeholders = ", ".join(["%s"] * len(values))
                    sql_insert = f"INSERT INTO ms01_customerlist ({column_names}) VALUES ({placeholders})"
                    cursor.execute(sql_insert, values)
                    
                    conn.commit()
                    flash(f"顧客コード {customer_code} を発行し、登録しました。", "success")
                    return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))

            # ###【登録申請】ボタンが押された場合 → 確認画面へ ###
            elif action == "request_new_approval":
                approvers = get_approvers(conn)
                return render_template(
                    "shared/new_confirm.html", 
                    form_data=form_data, 
                    approvers=approvers,
                    submit_url=url_for('customerlist.customer_new'),
                    final_action_value="submit_new_approval"
                )

            # ###【最終的な登録申請】確認画面のボタンが押された場合 ###
            elif action == "submit_new_approval":
                with conn.cursor() as cursor:
                    # (この部分は前回の修正で問題ありません)
                    # ...
                    pass 

        # --- [GET] 新規登録ページを最初に表示する時の処理 ---
        else: # request.method == 'GET' の場合
            form_data = {f: "" for f in field_names}
            form_data['registration_shain'] = session.get('shain_name', '')
            approvers = get_approvers(conn)
            button_config = {"show_instant_register": True, "show_approval_register": True}
            return render_template(
                "masters/customer_form.html", 
                form_data=form_data, 
                mode="create", 
                page_title="新規 顧客登録", 
                button_config=button_config,
                approvers=approvers
            )
    
    finally:
        if conn: conn.close()
# ==============================================================================
# 既存顧客の編集・更新・削除・承認申請機能
# ==============================================================================
@customerlist_bp.route("/masters/customer/<customer_code>", methods=["GET", "POST"])
def customer_edit(customer_code):
    conn = get_db_connection()
    try:
        # --- [POST] フォームのボタンが押された時の処理 ---
        if request.method == "POST":
            # (この部分は、次の「取下げ確認画面」のステップで一緒に修正します)
            action = request.form.get("action")
            
            # ###【承認】処理 ###
            if action == 'approve':
                approval_request_id = request.form.get('approval_request_id')
                with conn.cursor() as cursor:
                    cursor.execute("SELECT request_data FROM ts51_approval_requests WHERE id = %s", (approval_request_id,))
                    request_data_json = cursor.fetchone()['request_data']
                    form_data = json.loads(request_data_json, default=json_serial)

                    update_parts = []
                    values = []
                    for f in field_names:
                        if f in ["registration_date", "registration_shain", "update_date", "update_shain"]: continue
                        values.append(form_data.get(f))
                        update_parts.append(f"{f} = %s")
                    
                    update_parts.append("registration_status = %s")
                    values.append(1) # 1: 登録済
                    update_parts.append("update_date = %s")
                    values.append(datetime.datetime.now())
                    update_parts.append("update_shain = %s")
                    values.append(session.get('shain_name', '不明なユーザー'))
                    values.append(customer_code)

                    sql = f"UPDATE ms01_customerlist SET {', '.join(update_parts)} WHERE customer_code = %s"
                    cursor.execute(sql, values)
                    cursor.execute("UPDATE ts51_approval_requests SET status = 1 WHERE id = %s", (approval_request_id,))
                    conn.commit()
                flash(f"顧客情報（{customer_code}）の申請を承認しました。", "success")
                return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))

            # ###【差戻し】処理 ###
            elif action == 'reject':
                approval_request_id = request.form.get('approval_request_id')
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE ms01_customerlist SET registration_status = 3 WHERE customer_code = %s", (customer_code,))
                    cursor.execute("UPDATE ts51_approval_requests SET status = 2 WHERE id = %s", (approval_request_id,))
                    conn.commit()
                flash(f"申請を差戻しました。", "warning")
                return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))

            # ###【取下げ】処理 ###
            elif action == 'withdraw_request':
                approval_request_id = request.form.get('approval_request_id')
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE ms01_customerlist SET registration_status = 1 WHERE customer_code = %s", (customer_code,))
                    cursor.execute("UPDATE ts51_approval_requests SET status = 3 WHERE id = %s", (approval_request_id,))
                    conn.commit()
                flash(f"申請を取り下げました。", "info")
                return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))
            
            # ###【既存の更新・申請確認】処理は、この後のステップで統合します ###
            # ...

        # --- [GET] 編集ページを最初に表示する時の処理 ---
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ms01_customerlist WHERE customer_code = %s", (customer_code,))
            customer = cursor.fetchone()
        
        if not customer:
            flash("指定された顧客が見つかりませんでした。", "error")
            return redirect(url_for("customerlist.show_customerlist"))
        
        approval_request = None
        button_config = {}
        customer_status = customer.get('registration_status')

        # ステータスが「2: 承認待ち」の場合
        if customer_status == 2:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM ts51_approval_requests WHERE target_id = %s AND status = 0 ORDER BY created_at DESC LIMIT 1"
                cursor.execute(sql, (customer_code,))
                approval_request = cursor.fetchone()

            if approval_request:
                current_user_shain_code = session.get('shain_code')
                current_user_role = session.get('role')
                if current_user_shain_code == approval_request['requester_id']:
                    button_config = {"show_withdraw": True, "show_close": True}
                elif current_user_role in [1, 2, 3, 4, 5]:
                    button_config = {"show_approve": True, "show_reject": True, "show_close": True}
                else:
                    button_config = {"show_close": True}
            else:
                button_config = {"show_close": True}
                flash("承認待ちの状態ですが、有効な申請情報が見つかりませんでした。", "warning")
        
        # ステータスが「3: 差戻し」または通常時
        else:
            button_config = {"show_instant_update": True, "show_approval_update": True, "show_instant_delete": True, "show_approval_delete": True}
            if customer_status == 3:
                with conn.cursor() as cursor:
                    sql = "SELECT * FROM ts51_approval_requests WHERE target_id = %s AND status = 2 ORDER BY created_at DESC LIMIT 1"
                    cursor.execute(sql, (customer_code,))
                    approval_request = cursor.fetchone()

        # テンプレートに渡すためのデータ整形
        for field in ["registration_date", "update_date"]:
            if customer.get(field) and isinstance(customer.get(field), (datetime.date, datetime.datetime)):
                customer[field] = customer[field].strftime('%Y-%m-%dT%H:%M')
        # (その他のデータ整形処理もここに含まれます)
        
        return render_template(
            "masters/customer_form.html", 
            form_data=customer, 
            mode="edit", 
            button_config=button_config,
            approval_request=approval_request
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
                requester_id = 'admin' # 仮
                sql_request = """
                    INSERT INTO ts51_approval_requests (target_table, target_id, request_type, request_data, requester_id, approver_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s, '申請中')
                """
                cursor.execute(sql_request, ('ms01_customerlist', customer_code, '削除', None, requester_id, approver_id))
                cursor.execute("UPDATE ms01_customerlist SET registration_status = %s WHERE customer_code = %s", (6, customer_code))
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

