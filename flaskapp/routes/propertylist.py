import datetime
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flaskapp.utils.db import get_db_connection
from flaskapp.common import constants
from flaskapp.services.logging_service import log_action

propertylist_bp = Blueprint("propertylist", __name__)

# ==============================================================================
# ヘルパー関数
# ==============================================================================
def get_property_fields():
    """ms02_propertylistテーブルのカラム名リストを返します"""
    return [
        "property_name", "property_name_kana", "property_postalcode", "property_prefecture",
        "property_city", "property_address", "landlord_agency_branch_cd", "landlord_name",
        "property_remarks", "registration_date", "registration_shain", "update_date",
        "update_shain", "registration_status", "assignor_code", "assignee_code"
    ]

def get_property_field_labels():
    """物件の日本語項目名リストを返します"""
    return {
        "property_code": "物件コード",
        "property_name": "物件名",
        "property_name_kana": "物件名カナ",
        "property_postalcode": "郵便番号",
        "property_prefecture": "都道府県",
        "property_city": "市区町村",
        "property_address": "番地",
        "landlord_agency_branch_cd": "家主・管理会社コード",
        "landlord_name": "家主・管理会社名",
        "property_remarks": "備考",
        "registration_date": "登録日",
        "registration_shain": "登録者",
        "update_date": "更新日",
        "update_shain": "更新者",
        "registration_status": "登録状況",
        "assignor_code": "担当者",
        "assignee_code": "アサイン先"
    }

# ==============================================================================
# 物件情報の一覧表示・検索機能
# ==============================================================================
@propertylist_bp.route("/masters/propertylist")
def show_propertylist():
    # 検索フィルターの値を取得
    filters = {
        "property_code": request.args.get("property_code", "").strip(),
        "property_name": request.args.get("property_name", "").strip(),
        "property_name_kana": request.args.get("property_name_kana", "").strip(),
        "address": request.args.get("address", "").strip(), # 住所一括検索用
        "registration_status": request.args.get("registration_status", "").strip(),
        "registration_date_from": request.args.get("registration_date_from", "").strip(),
        "registration_date_to": request.args.get("registration_date_to", "").strip(),
    }
    has_search = any(filters.values())
    
    # ページネーションの設定
    page = int(request.args.get("page", "1"))
    limit = int(request.args.get("limit", "20"))
    offset = (page - 1) * limit
    max_results = int(request.args.get("max_results", "100"))

    # ソート情報
    sort_by = request.args.get("sort_by")
    sort_order = request.args.get("sort_order")

    # 安全なORDER BY句を組み立て
    allowed_sort_columns = ['property_code', 'property_name', 'property_name_kana', 'registration_status', 'registration_date']
    # デフォルトのソート順を昇順に変更
    order_by_sql = "ORDER BY property_code ASC" 
    
    if sort_by in allowed_sort_columns and sort_order in ['asc', 'desc']:
        order_by_sql = f"ORDER BY {sort_by} {sort_order.upper()}"

    # DB接続
    conn = get_db_connection()
    if not conn:
        flash("データベースに接続できませんでした。", "danger")
        return render_template("masters/propertylist.html", properties=[], total=0, page=1, limit=limit, total_pages=0, filters=filters, registration_status=constants.registration_status_MAP)

    results = []
    total = 0
    try:
        # 検索条件の組み立て
        where_clauses = ["1=1"]
        params = {}
        if filters["property_code"]:
            where_clauses.append("property_code LIKE %(property_code)s")
            params['property_code'] = f"%{filters['property_code']}%"
        if filters["property_name"]:
            where_clauses.append("property_name LIKE %(property_name)s")
            params['property_name'] = f"%{filters['property_name']}%"
        if filters["property_name_kana"]:
            where_clauses.append("property_name_kana LIKE %(property_name_kana)s")
            params['property_name_kana'] = f"%{filters['property_name_kana']}%"
        if filters["address"]:
            # 住所は都道府県・市区町村・番地をまとめて検索
            where_clauses.append("(property_prefecture LIKE %(address)s OR property_city LIKE %(address)s OR property_address LIKE %(address)s)")
            params['address'] = f"%{filters['address']}%"
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
            # 総件数を取得
            count_sql = f"SELECT COUNT(*) as total FROM ms02_propertylist WHERE {where_sql}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total'] or 0

            if total > max_results:
                flash(f"検索結果が{max_results}件を超えました。最初の{max_results}件を表示します。", "warning")
                total = max_results

            if total > 0:
                params_with_limit = params.copy()
                params_with_limit['limit'] = limit
                params_with_limit['offset'] = offset
                
                # SQLファイルを読み込む
                try:
                    with open('flaskapp/sql/properties/select_propertylist.sql', 'r', encoding='utf-8') as f:
                        base_sql = f.read()
                except FileNotFoundError:
                    flash("SQL定義ファイルが見つかりません。", "danger")
                    return redirect(url_for('main.index'))

                sql = f"{base_sql.strip().rstrip(';')} WHERE {where_sql} {order_by_sql} LIMIT %(limit)s OFFSET %(offset)s"
                
                cursor.execute(sql, params_with_limit)
                results = cursor.fetchall()

    except Exception as e:
        flash(f"データ取得中にエラーが発生しました: {e}", "danger")
    finally:
        if conn: conn.close()
            
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    return render_template(
        "masters/propertylist.html",
        properties=results, 
        total=total, 
        page=page, 
        limit=limit, 
        total_pages=total_pages,
        filters=filters, 
        has_search=has_search, 
        selected_limit=str(limit),
        registration_status=constants.registration_status_MAP,
        selected_max_results=str(max_results),
        sort_by=sort_by,
        sort_order=sort_order
    )

# ==============================================================================
# 新規物件の登録機能
# ==============================================================================
@propertylist_bp.route("/masters/property/new", methods=["GET", "POST"])
def property_new():
    """新規物件の登録"""
    conn = get_db_connection()
    try:
        user_role = session.get('role', 0)
        button_config = {}
        # システム管理者、社員A, B の場合に「登録」ボタンを表示
        if user_role in [1, 3, 4]:
            button_config["show_instant_register"] = True

        if request.method == "POST":
            field_names = get_property_fields()
            form_data = {f: request.form.get(f, "").strip() for f in field_names}
            
            if not form_data.get("property_name"):
                flash("物件名を入力してください。", "error")
                return render_template("masters/property_form.html", mode="create", form_data=form_data, button_config=button_config)
            
            with conn.cursor() as cursor:
                # 物件コードの採番 (B + 6桁)
                cursor.execute("SELECT MAX(CAST(SUBSTRING(property_code, 2) AS UNSIGNED)) AS max_num FROM ms02_propertylist WHERE property_code LIKE 'B%'")
                max_num = cursor.fetchone()['max_num']
                property_code = f"B{(max_num or 0) + 1:06d}"

                form_data['registration_shain'] = session.get('shain_name', '不明')
                form_data['registration_date'] = datetime.datetime.now()
                form_data['registration_status'] = 1 # 登録済み

                values = [property_code]
                for f in field_names:
                    val = form_data.get(f, "")
                    values.append(val if val != "" else None)
                
                column_names = ", ".join(["property_code"] + field_names)
                sql_insert = f"INSERT INTO ms02_propertylist ({column_names}) VALUES ({', '.join(['%s']*len(values))})"
                cursor.execute(sql_insert, values)
                conn.commit()

                log_action(
                    target_type=4,  # 4: 物件マスタ
                    target_id=property_code,
                    action_source=2,
                    action_type=1,
                    action_details={'message': f'物件 {property_code} が新規登録されました。'}
                )

            flash(f"物件コード {property_code} で登録しました。", "success")
            return redirect(url_for("propertylist.property_edit", property_code=property_code))
        
        form_data = {f: "" for f in get_property_fields()}
        return render_template("masters/property_form.html", mode="create", form_data=form_data, button_config=button_config)
    
    finally:
        if conn: conn.close()

# ==============================================================================
# 既存物件の編集・更新・削除機能
# ==============================================================================
@propertylist_bp.route("/masters/property/<property_code>", methods=["GET", "POST"])
def property_edit(property_code):
    conn = get_db_connection()
    try:
        # ユーザーのロールをセッションから取得
        user_role = session.get('role', 0)

        # デフォルトでは全ての操作ボタンを非表示
        button_config = {
            "show_instant_update": False,
            "show_instant_delete": False,
        }

        # ロールに基づいてボタンの表示を決定
        if user_role in [1, 3]:  # 1:システム管理者, 3:社員A
            button_config["show_instant_update"] = True
            button_config["show_instant_delete"] = True
        elif user_role == 4:  # 4:社員B
            button_config["show_instant_update"] = True

        if request.method == "POST":
            action = request.form.get("action")
            field_names = get_property_fields()

            if action == "update_instant":
                form_data = {f: request.form.get(f, "").strip() for f in field_names}
                
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM ms02_propertylist WHERE property_code = %s", (property_code,))
                    before_data = cursor.fetchone()

                if not before_data:
                    flash("更新対象のデータが見つかりません。", "error")
                    return redirect(url_for('propertylist.show_propertylist'))

                changes = []
                field_labels = get_property_field_labels()
                for field in field_names:
                    before_val = before_data.get(field, '')
                    after_val = form_data.get(field, '')
                    
                    # 日付はフォーマットを揃えて比較
                    if isinstance(before_val, (datetime.datetime, datetime.date)):
                        before_str = before_val.strftime('%Y-%m-%dT%H:%M') if isinstance(before_val, datetime.datetime) else before_val.isoformat()
                    else:
                        before_str = str(before_val or '')

                    after_str = str(after_val or '')

                    if before_str != after_str:
                        changes.append({"label": field_labels.get(field, field), "before": before_str, "after": after_str})

                if not changes:
                    flash("変更された項目がありません。", "info")
                    return redirect(url_for("propertylist.property_edit", property_code=property_code))
                
                return render_template("shared/update_confirm.html", changes=changes, form_data=form_data,
                    submit_url=url_for('propertylist.property_edit', property_code=property_code),
                    is_approval_flow=False, final_action_value="submit_update_instant")

            elif action == "submit_update_instant":
                form_data = {f: request.form.get(f, "").strip() for f in field_names}
                form_data['update_date'] = datetime.datetime.now()
                form_data['update_shain'] = session.get('shain_name', '不明')

                form_data['registration_status'] = 1

                values = []
                for f in field_names:
                    val = form_data.get(f, "")
                    values.append(val if val != "" else None)
                values.append(property_code)

                update_clause = ", ".join(f"{col} = %s" for col in field_names)
                sql = f"UPDATE ms02_propertylist SET {update_clause} WHERE property_code = %s"
                
                with conn.cursor() as cursor:
                    cursor.execute(sql, values)
                    conn.commit()
                    log_action(target_type=4, target_id=property_code, action_source=2, action_type=2,
                               action_details=json.loads(request.form.get('changes_json', '[]')))
                    
                return render_template("shared/action_done.html", action_label="更新")

            elif action == "delete_instant":
                # 物件に紐づくデータがあるかチェック（将来的に実装）
                # ▼▼▼ TODO: 将来、申込テーブルに物件コードが追加されたら、以下のコメントを解除する ▼▼▼
            # with conn.cursor() as cursor:
            #     cursor.execute("SELECT application_number FROM tr01_applicationlist WHERE property_code = %s", (property_code,))
            #     related_applications = cursor.fetchall()
            #
            # if related_applications:
            #     deletable = False
            #     app_numbers = ", ".join([app['application_number'] for app in related_applications])
            #     message = f"この物件（{property_code}）は申込番号 ({app_numbers}) と紐づいているため、削除できません。"
            # else:
            #     deletable = True
            #     message = f"本当に「{property_code}」を削除しますか？"
            # ▲▲▲ ここまで ▲▲▲
                deletable = True
                message = f"本当に「{property_code}」を削除しますか？"
                
                return render_template("shared/delete_confirm.html", message=message, deletable=deletable,
                    submit_url=url_for('propertylist.property_delete_confirmed', property_code=property_code),
                    is_approval_flow=False, final_action_value="submit_delete_instant")

        # GETリクエスト
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ms02_propertylist WHERE property_code = %s", (property_code,))
            property_data = cursor.fetchone()

        if not property_data:
            flash("指定された物件が見つかりませんでした。", "error")
            return redirect(url_for("propertylist.show_propertylist"))
        
        # 日付をdatetime-local形式に変換
        for field in ["registration_date", "update_date"]:
            if property_data.get(field) and isinstance(property_data.get(field), datetime.datetime):
                property_data[field] = property_data[field].strftime('%Y-%m-%dT%H:%M')
        
        for key, value in property_data.items():
            if value is None:
                property_data[key] = ''

        return render_template("masters/property_form.html", form_data=property_data, mode="edit", button_config=button_config)

    finally:
        if conn.open: conn.close()

# ==============================================================================
# 物件の削除実行機能
# ==============================================================================
@propertylist_bp.route("/masters/property/delete/<property_code>", methods=["POST"])
def property_delete_confirmed(property_code):
    conn = get_db_connection()
    try:
        if request.form.get("action") == "submit_delete_instant":
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM ms02_propertylist WHERE property_code = %s", (property_code,))
                deleted_data = cursor.fetchone()
                cursor.execute("DELETE FROM ms02_propertylist WHERE property_code = %s", (property_code,))
                conn.commit()

                if deleted_data:
                    for key, value in deleted_data.items():
                        if isinstance(value, (datetime.date, datetime.datetime)):
                            deleted_data[key] = value.isoformat()
                    log_action(target_type=4, target_id=property_code, action_source=2, action_type=3,
                               action_details={'deleted_data': deleted_data})

            return render_template("shared/action_done.html", action_label="削除")
    except Exception as e:
        flash(f"処理中にエラーが発生しました: {e}", "error")
    finally:
        if conn.open: conn.close()
    return redirect(url_for('propertylist.show_propertylist'))