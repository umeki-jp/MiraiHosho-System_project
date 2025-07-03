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
        if request.method == "POST":
            action = request.form.get("action")
            form_data = {f: request.form.get(f, "").strip() for f in field_names}
            
            if action == "request_new_approval":
                if not form_data.get("name"):
                    flash("名前を入力してください。", "error")
                    return render_template("masters/customer_form.html", mode="create", form_data=form_data, button_config={"show_approval_register": True}, approvers=get_approvers(conn))
                return render_template("shared/new_confirm.html", form_data=form_data, approvers=get_approvers(conn), submit_url=url_for('customerlist.customer_new'), final_action_value="submit_new_approval")

            elif action == "submit_new_approval":
                with conn.cursor() as cursor:
                    cursor.execute("SELECT MAX(CAST(SUBSTRING(customer_code, 2) AS UNSIGNED)) AS max_num FROM ms01_customerlist WHERE customer_code LIKE 'C%'")
                    max_num = cursor.fetchone()['max_num']
                    customer_code = f"C{(max_num or 0) + 1:07d}"
                    form_data.update({'registration_shain': session.get('shain_name', '不明なユーザー'),'registration_date': datetime.datetime.now(),'registration_status': 2})
                    values = [customer_code]
                    for f in field_names:
                        val = form_data.get(f, "")
                        values.append(None if (f.endswith("Date") or f.endswith("age")) and val == "" else val)
                    column_names = ", ".join(["customer_code"] + field_names)
                    sql_insert = f"INSERT INTO ms01_customerlist ({column_names}) VALUES ({', '.join(['%s']*len(values))})"
                    cursor.execute(sql_insert, values)
                    
                    approver_id = request.form.get('approver_id')
                    requester_id = session.get('shain_code', 'UNKNOWN')
                    sql_request = "INSERT INTO ts51_approval_requests (target_table, target_id, request_type, request_data, requester_id, approver_id, status) VALUES (%s, %s, %s, %s, %s, %s, 0)"
                    request_data_json = json.dumps(form_data, ensure_ascii=False, default=json_serial)
                    cursor.execute(sql_request, ('ms01_customerlist', customer_code, '新規', request_data_json, requester_id, approver_id))
                    conn.commit()
                flash("顧客情報の登録を申請しました。", "success")
                return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))
        
        # GETリクエスト
        return render_template("masters/customer_form.html", mode="create", form_data={f: "" for f in field_names}, button_config={"show_approval_register": True}, approvers=get_approvers(conn), approval_request=None)
    finally:
        if conn: conn.close()

# ==============================================================================
# 顧客の削除・削除申請の実行機能
# ==============================================================================
@customerlist_bp.route("/masters/customer/<customer_code>", methods=["GET", "POST"])
def customer_edit(customer_code):
    conn = get_db_connection()
    try:
        # (POST処理は、この後のステップで完成させます)
        if request.method == "POST":
            action = request.form.get("action")
            
            # ###【更新申請】ボタンが押された場合 → 確認画面へ ###
            if action == 'request_update_approval':
                form_data = {f: request.form.get(f, "").strip() for f in field_names}
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM ms01_customerlist WHERE customer_code = %s", (customer_code,))
                    before_data = cursor.fetchone()
                changes = []
                field_labels = get_field_labels()
                for field in field_names:
                    before_val = str(before_data.get(field, '') or '')
                    after_val = str(form_data.get(field, '') or '')
                    if field in ["registration_date", "update_date"] and before_data.get(field):
                        before_val = before_data.get(field).strftime('%Y-%m-%dT%H:%M')
                    if before_val != after_val:
                        changes.append({"label": field_labels.get(field, field), "before": before_val, "after": after_val})
                if not changes:
                    flash("変更された項目がありません。", "info")
                    return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))
                return render_template("shared/update_confirm.html", changes=changes, form_data=form_data, submit_url=url_for('customerlist.customer_edit', customer_code=customer_code), approvers=get_approvers(conn), is_approval_flow=True, final_action_value="submit_update_approval")

            # ###【削除申請】ボタンが押された場合 → 確認画面へ ###
            elif action == 'request_delete_approval':
                # (この部分は後ほど削除機能全体を実装する際に完成させます)
                flash("削除申請機能は現在実装中です。", "info")
                return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))

        # [GET] ページを最初に表示する時の処理
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ms01_customerlist WHERE customer_code = %s", (customer_code,))
            customer = cursor.fetchone()
        if not customer:
            flash("指定された顧客が見つかりませんでした。", "error")
            return redirect(url_for("customerlist.show_customerlist"))
        
        approval_request, button_config = None, {}
        customer_status = customer.get('registration_status')

        if customer_status == 2: # 承認待ち
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM ts51_approval_requests WHERE target_id = %s AND status = 0 ORDER BY created_at DESC LIMIT 1", (customer_code,))
                approval_request = cursor.fetchone()
            if approval_request:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT shain_name FROM ms_shainlist WHERE shain_code = %s", (approval_request.get('requester_id'),))
                    approval_request['requester_name'] = (res := cursor.fetchone()) and res.get('shain_name') or ''
                    cursor.execute("SELECT shain_name FROM ms_shainlist WHERE shain_code = %s", (approval_request.get('approver_id'),))
                    approval_request['approver_name'] = (res := cursor.fetchone()) and res.get('shain_name') or ''
                if approval_request.get('request_type') == '更新':
                    changes = []
                    field_labels = get_field_labels()
                    before_data, after_data = customer, json.loads(approval_request['request_data'])
                    for field in field_names:
                        before_val, after_val = str(before_data.get(field, '') or ''), str(after_data.get(field, '') or '')
                        if field in ["registration_date", "update_date"] and before_data.get(field):
                            before_val = before_data.get(field).strftime('%Y-%m-%dT%H:%M')
                        if before_val != after_val:
                            changes.append({"label": field_labels.get(field, field), "before": before_val, "after": after_val})
                    approval_request['changes'] = changes
                
                current_user_shain_code, current_user_role = session.get('shain_code'), session.get('role')
                if current_user_shain_code == approval_request['requester_id']:
                    button_config = {"show_withdraw": True, "show_close": True}
                elif current_user_role in [1, 2, 3, 4, 5]:
                    button_config = {"show_approve": True, "show_reject": True, "show_close": True}
                else: button_config = {"show_close": True}
            else: button_config = {"show_close": True}
        else: # 登録済(1), 差戻し(3)など
            button_config = {"show_approval_update": True, "show_approval_delete": True, "show_close": True}
            if customer_status == 3:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM ts51_approval_requests WHERE target_id = %s AND status = 2 ORDER BY created_at DESC LIMIT 1", (customer_code,))
                    approval_request = cursor.fetchone()
        
        return render_template("masters/customer_form.html", mode="edit", form_data=customer, button_config=button_config, approval_request=approval_request, approvers=get_approvers(conn))
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