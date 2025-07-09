import datetime
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flaskapp.utils.db import get_db_connection
from flaskapp.utils.ms01_customerlist_fields import field_names 
from flaskapp.common import constants
from flaskapp.services.logging_service import log_action

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
        "registration_shain": "登録者", "update_date": "更新日", "update_shain": "更新者", "registration_status": "登録状況","assignor_code": "担当者","assignee_code": "アサイン先"
    }

# ==============================================================================
# 顧客情報の一覧表示・検索機能
# ==============================================================================

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

    try:
        max_results = int(request.args.get("max_results", "100"))
    except (ValueError, TypeError):
        max_results = 100

    # ▼▼▼【1. ソート情報を受け取る】▼▼▼
    sort_by = request.args.get("sort_by")
    sort_order = request.args.get("sort_order")

    # ▼▼▼【2. 安全なORDER BY句を組み立てる】▼▼▼
    # SQLインジェクションを防ぐため、ソート可能な列をホワイトリストで定義
    allowed_sort_columns = ['customer_code', 'name', 'name_kana', 'individual_birthdate', 'typeofcustomer', 'customer_rank', 'registration_date']
    
    # デフォルトのソート順
    order_by_sql = "ORDER BY customer_code DESC" 
    
    if sort_by in allowed_sort_columns and sort_order in ['asc', 'desc']:
        order_by_sql = f"ORDER BY {sort_by} {sort_order.upper()}"

    # データベース接続
    conn = get_db_connection()

    if not conn:
        # ... 接続失敗時の処理 (変更なし) ...
        flash("データベースに接続できませんでした。管理者にお問い合わせください。", "danger")
        return render_template(
            "masters/customerlist.html", customers=[], total=0, page=1, limit=limit, 
            total_pages=0, filters=filters, has_search=has_search, 
            selected_limit=str(limit), 
            registration_status=constants.registration_status_MAP,
            customer_rank_map=constants.CUSTOMER_RANK_MAP,
            selected_max_results=str(max_results)
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
        # ▼▼▼ 電話番号と勤務先の検索ロジックを有効化 ▼▼▼
        if filters["tel"]:
            where_clauses.append("(individual_tel1 LIKE %(tel)s OR individual_tel2 LIKE %(tel)s OR corporate_tel1 LIKE %(tel)s OR corporate_tel2 LIKE %(tel)s)")
            params['tel'] = f"%{filters['tel']}%"
        if filters["workplace"]:
            where_clauses.append("individual_workplace LIKE %(workplace)s")
            params['workplace'] = f"%{filters['workplace']}%"
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
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
            params_for_count = params.copy()
            params_for_count['max_limit'] = max_results + 1
            count_sql = f"SELECT COUNT(*) as total FROM ms01_customerlist WHERE {where_sql} LIMIT %(max_limit)s"
            cursor.execute(count_sql, params_for_count)
            count_result = cursor.fetchone()['total'] or 0

            if count_result > max_results:
                total = max_results
                flash(f"検索結果が{max_results}件を超えました。最初の{max_results}件を表示します。条件を絞り込んでください。", "warning")
            else:
                total = count_result

            if total > 0:
                params_with_limit = params.copy()
                params_with_limit['limit'] = limit
                params_with_limit['offset'] = offset
                
                # .sqlファイルを読み込む処理
                try:
                    with open('flaskapp/sql/customers/select_customerlist.sql', 'r', encoding='utf-8') as f:
                        base_sql = f.read()
                except FileNotFoundError:
                    flash("SQL定義ファイルが見つかりません。管理者にご連絡ください。", "danger")
                    return redirect(url_for('main.index'))

                # 読み込んだベースSQLに、動的な条件を結合する
                sql = f"{base_sql.strip().rstrip(';')} WHERE {where_sql} {order_by_sql} LIMIT %(limit)s OFFSET %(offset)s"
                
                cursor.execute(sql, params_with_limit)
                results = cursor.fetchall()
    except Exception as e:
        flash(f"データの取得中にエラーが発生しました: {e}", "danger")
        total = 0
        results = []
    finally:
        if conn:
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
        registration_status=constants.registration_status_MAP,
        customer_rank_map=constants.CUSTOMER_RANK_MAP,
        selected_max_results=str(max_results),
        # ▼▼▼【4. ソート状態をテンプレートに渡す】▼▼▼
        sort_by=sort_by,
        sort_order=sort_order
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
    )
# ==============================================================================
# 新規顧客の登録・登録申請機能
# ==============================================================================
@customerlist_bp.route("/masters/customer/new", methods=["GET", "POST"])
def customer_new():
    """新規顧客の登録（承認なし）"""
    conn = get_db_connection()
    try:
        # --- 1. まず、役割に応じて表示するボタンを決定する ---
        button_config = {}
        user_role = session.get('role', 0)
        # グループA (システム管理), 社員A, B の場合にのみ「登録」ボタンを表示
        if user_role in [1, 3, 4]:
            button_config["show_instant_register"] = True

        # --- 2. [POST] 「登録」ボタンが押された時の処理 ---
        if request.method == "POST":
            # 権限チェック
            if not button_config.get("show_instant_register"):
                flash("この操作を行う権限がありません。", "danger")
                return redirect(url_for("customerlist.show_customerlist"))

            form_data = {f: request.form.get(f, "").strip() for f in field_names}
            
            # 入力チェック
            if not form_data.get("name"):
                flash("名前を入力してください。", "error")
                return render_template("masters/customer_form.html", mode="create", form_data=form_data, button_config=button_config)
            
            # 日付の妥当性チェック
            date_fields_to_check = ["individual_birthdate", "corporate_foundationdate"]
            for field in date_fields_to_check:
                date_str = form_data.get(field)
                if date_str:
                    try:
                        datetime.datetime.strptime(date_str, '%Y%m%d')
                    except ValueError:
                        flash(f"入力された日付（{get_field_labels().get(field)}）が正しくありません。(例: 20250131)", "error")
                        return render_template("masters/customer_form.html", mode="create", form_data=form_data, button_config=button_config)

            # データベース登録処理
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(CAST(SUBSTRING(customer_code, 2) AS UNSIGNED)) AS max_num FROM ms01_customerlist WHERE customer_code LIKE 'C%'")
                max_num = cursor.fetchone()['max_num']
                customer_code = f"C{(max_num or 0) + 1:07d}"

                form_data['registration_shain'] = session.get('shain_name', '不明なユーザー')
                form_data['registration_date'] = datetime.datetime.now()
                form_data['registration_status'] = 1

                values = [customer_code]
                datetime_fields = ["individual_birthdate", "corporate_foundationdate", "registration_date", "update_date"]
                integer_fields = ["individual_age", "customer_rank"]
                for f in field_names:
                    val = form_data.get(f, "")
                    if (f in datetime_fields or f in integer_fields) and val == "":
                        values.append(None)
                    else:
                        values.append(val)
                
                column_names = ", ".join(["customer_code"] + field_names)
                sql_insert = f"INSERT INTO ms01_customerlist ({column_names}) VALUES ({', '.join(['%s']*len(values))})"
                cursor.execute(sql_insert, values)
                conn.commit()

                # ▼▼▼ ログ記録処理を追加 ▼▼▼
                log_action(
                    target_type=3,  # 3: 顧客マスタ
                    target_id=customer_code,
                    action_source=2, # 2: ユーザー操作
                    action_type=1,  # 1: 登録
                    action_details={'message': f'顧客 {customer_code} が新規登録されました。'}
                )

            # 顧客コードを発行し、登録した後に1回だけメッセージを表示
            flash(f"顧客コード {customer_code} を発行し、登録しました。", "success")
            return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))
        
        # --- 3. [GET] 新規登録ページを最初に表示する時の処理 ---
        form_data = {f: "" for f in field_names}
        # customer_rankの初期値を0に設定
        form_data['customer_rank'] = 0
        
        return render_template(
            "masters/customer_form.html", 
            mode="create", 
            form_data=form_data,  # 修正したform_dataを渡す
            button_config=button_config,
            customer_rank_list=constants.CUSTOMER_RANK_LIST
        )
    
    finally:
        if conn: conn.close()

# ==============================================================================
# 既存顧客の編集・更新・削除機能
# ==============================================================================
@customerlist_bp.route("/masters/customer/<customer_code>", methods=["GET", "POST"])
def customer_edit(customer_code):
    conn = get_db_connection()
    try:
        # ボタン設定：承認関連のボタンを非表示にする
        button_config = {
            "show_instant_update": True, "show_approval_update": False,
            "show_instant_delete": True, "show_approval_delete": False
        }
        # ユーザーのロールを取得
        user_role = session.get('role', 0)

        # デフォルトでは全ての操作ボタンを非表示（閲覧のみ）
        button_config = {
            "show_instant_update": False,
            "show_instant_delete": False,
            "show_approval_update": False,
            "show_approval_delete": False
        }

        # ロールに基づいてボタンの表示を決定
        if user_role in [1, 3]:  # 1:システム管理者, 3:社員A
            button_config["show_instant_update"] = True
            button_config["show_instant_delete"] = True
        elif user_role == 4:  # 4:社員B
            button_config["show_instant_update"] = True

        if request.method == "POST":
            action = request.form.get("action")

            # --- 即時更新の確認画面表示 ---
            if action == "update_instant":
                form_data = {f: request.form.get(f, "").strip() for f in field_names}

                # ▼▼▼ 日付妥当性チェック ▼▼▼
                birth_date_str = form_data.get("individual_birthdate")
                if birth_date_str:
                    try:
                        datetime.datetime.strptime(birth_date_str, '%Y%m%d')
                    except ValueError:
                        flash("個人_生年月日に入力された日付が正しくありません。(例: 19800230)", "error")
                        return render_template("masters/customer_form.html", form_data=form_data, mode="edit", button_config=button_config)
                # ▲▲▲ 日付妥当性チェックここまで ▲▲▲

                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM ms01_customerlist WHERE customer_code = %s", (customer_code,))
                    before_data = cursor.fetchone()

                if not before_data:
                    flash("更新対象の顧客データが見つかりません。", "error")
                    return redirect(url_for('customerlist.show_customerlist'))

                # ▼▼▼ 変更点の比較ロジック ▼▼▼
                changes = []
                field_labels = get_field_labels()

                for field in field_names:
                    before_val = before_data.get(field)
                    after_val = form_data.get(field)

                    before_str = ""
                    after_str = ""

                    # ▼▼▼【ここから修正】▼▼▼
                    # 'customer_rank' フィールドの場合、数値を日本語に変換
                    if field == "customer_rank":
                        before_str = constants.CUSTOMER_RANK_MAP.get(before_val, "未設定")
                        
                        # フォームからの値は文字列なので整数に変換してからMAPを引く
                        if after_val:
                            try:
                                after_str = constants.CUSTOMER_RANK_MAP.get(int(after_val), "未設定")
                            except (ValueError, TypeError):
                                after_str = "不正な値" # 念のため
                        else:
                            after_str = "未設定"
                    
                    # 'customer_rank' 以外のフィールドは既存の処理
                    else:
                        # --- 既存の正規化処理 ---
                        if isinstance(before_val, datetime.datetime):
                            if field in ["registration_date", "update_date"]:
                                before_str = before_val.strftime('%Y-%m-%d %H:%M')
                            else: # 生年月日など
                                before_str = before_val.strftime('%Y%m%d')
                        elif isinstance(before_val, datetime.date):
                             before_str = before_val.strftime('%Y%m%d')
                        elif before_val is not None:
                            before_str = str(before_val)

                        if after_val:
                            if field in ["registration_date", "update_date"]:
                                after_str = after_val.replace('T', ' ')
                            else:
                                after_str = after_val

                    # --- 比較 ---
                    if before_str != after_str:
                        changes.append({
                            "label": field_labels.get(field, field),
                            "before": before_str,
                            "after": after_str
                        })

                # --- 変更がない場合の処理 ---
                if not changes:
                    flash("変更された項目がありません。", "info")
                    return redirect(url_for("customerlist.customer_edit", customer_code=customer_code))
                
                # 更新確認画面（承認ルートなし）を表示
                return render_template(
                    "shared/update_confirm.html",
                    changes=changes, form_data=form_data,
                    submit_url=url_for('customerlist.customer_edit', customer_code=customer_code),
                    is_approval_flow=False, # 承認フローではないことを明示
                    final_action_value="submit_update_instant"
                )

            # --- 即時更新の実行 ---
            elif action == "submit_update_instant":
                form_data = {f: request.form.get(f, "").strip() for f in field_names}
                # 1. 更新日時と更新者をサーバー側で設定
                form_data['update_date'] = datetime.datetime.now()
                form_data['update_shain'] = session.get('shain_name', '不明なユーザー')
                form_data['registration_status'] = 1

                # 2. フォームから送られてくる各種日付文字列をDB保存形式に変換
                # 生年月日など (YYYYMMDD -> YYYY-MM-DD)
                date_only_fields = ["individual_birthdate", "corporate_foundationdate"]
                for field in date_only_fields:
                    date_str = form_data.get(field)
                    if date_str:
                        try:
                            date_obj = datetime.datetime.strptime(date_str, '%Y%m%d')
                            form_data[field] = date_obj.strftime('%Y-%m-%d')
                        except ValueError:
                            form_data[field] = None
                
                # 登録日 (datetime-localからの YYYY-MM-DDTHH:MM -> datetimeオブジェクト)
                if form_data.get("registration_date"):
                    try:
                        form_data["registration_date"] = datetime.datetime.strptime(
                            form_data["registration_date"].replace('T', ' '), '%Y-%m-%d %H:%M'
                        )
                    except (ValueError, AttributeError):
                        form_data["registration_date"] = None
                with conn.cursor() as cursor:
                    datetime_fields = ["individual_birthdate", "corporate_foundationdate", "registration_date", "update_date"]
                    integer_fields = ["individual_age"]
                    values = []
                    for f in field_names:
                        val = form_data.get(f, "")
                        if (f in datetime_fields or f in integer_fields) and val == "":
                            values.append(None)
                        else:
                            values.append(val)
                    values.append(customer_code)
                    update_clause = ", ".join(f"{col} = %s" for col in field_names)
                    sql = f"UPDATE ms01_customerlist SET {update_clause} WHERE customer_code = %s"
                    cursor.execute(sql, values)
                    conn.commit()

                    # ▼▼▼ ログ記録処理を追加 ▼▼▼
                    log_action(
                        target_type=3,  # 3: 顧客マスタ
                        target_id=customer_code,
                        action_source=2, # 2: ユーザー操作
                        action_type=2,  # 2: 更新
                        action_details=json.loads(request.form.get('changes_json', '[]')) # 確認画面から変更内容を受け取る
                    )
                    
                return render_template("shared/action_done.html", action_label="更新")

            # --- 即時削除の確認画面表示 ---
            elif action == "delete_instant":
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

                # 削除確認画面（承認ルートなし）を表示
                return render_template(
                    "shared/delete_confirm.html",
                    message=message, deletable=deletable,
                    submit_url=url_for('customerlist.customer_delete_confirmed', customer_code=customer_code),
                    is_approval_flow=False, # 承認フローではないことを明示
                    final_action_value="submit_delete_instant"
                )

        # --- GETリクエスト（編集フォームの初期表示） ---
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ms01_customerlist WHERE customer_code = %s", (customer_code,))
            customer = cursor.fetchone()
        if not customer:
            flash("指定された顧客が見つかりませんでした。", "error")
            return redirect(url_for("customerlist.show_customerlist"))

        # 日付の表示形式を修正
        date_fields_to_format = ["individual_birthdate", "corporate_foundationdate", "registration_date", "update_date"]
        for field in date_fields_to_format:
            if customer.get(field) and isinstance(customer.get(field), (datetime.date, datetime.datetime)):
                if field in ["individual_birthdate", "corporate_foundationdate"]:
                    customer[field] = customer[field].strftime('%Y%m%d')
                else:
                    # 'datetime-local'のinputが要求する 'YYYY-MM-DDTHH:MM' 形式に変換
                    customer[field] = customer[field].strftime('%Y-%m-%dT%H:%M')

        for key, value in customer.items():
            if value is None:
                customer[key] = ''
        return render_template("masters/customer_form.html", form_data=customer, mode="edit", button_config=button_config, customer_rank_list=constants.CUSTOMER_RANK_LIST)

    finally:
        if conn.open:
            conn.close()
# ==============================================================================
# 顧客の削除実行機能
# ==============================================================================
@customerlist_bp.route("/masters/customer/delete/<customer_code>", methods=["POST"])
def customer_delete_confirmed(customer_code):
    conn = get_db_connection()
    try:
        action = request.form.get("action")

        # --- 即時削除の実行 ---
        if action == "submit_delete_instant":
            with conn.cursor() as cursor:
                # 関連データがある場合は削除できない、というチェックは確認画面側で実施済み
                cursor.execute("SELECT * FROM ms01_customerlist WHERE customer_code = %s", (customer_code,))
                deleted_customer_data = cursor.fetchone()
                cursor.execute("DELETE FROM ms01_customerlist WHERE customer_code = %s", (customer_code,))
                conn.commit()

                # ▼▼▼ ログ記録処理を追加 ▼▼▼
                if deleted_customer_data:
                    # 日付オブジェクトはJSONにできないため、文字列に変換
                    for key, value in deleted_customer_data.items():
                        if isinstance(value, (datetime.date, datetime.datetime)):
                            deleted_customer_data[key] = value.isoformat()

                    log_action(
                        target_type=3,  # 3: 顧客マスタ
                        target_id=customer_code,
                        action_source=2, # 2: ユーザー操作
                        action_type=3,  # 3: 削除
                        action_details={'deleted_data': deleted_customer_data}
                    )
            # 完了画面を表示
            return render_template("shared/action_done.html", action_label="削除")

    except Exception as e:
        flash(f"処理中にエラーが発生しました: {e}", "error")
    finally:
        if conn.open:
            conn.close()

    # エラー発生時などは一覧画面に戻す
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