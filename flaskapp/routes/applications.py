from flask import Blueprint, render_template, request, redirect, url_for
from flaskapp.utils.sql_loader import load_sql
import pymysql

applications_bp = Blueprint("applications", __name__)



@applications_bp.route("/applications/applicationslist")
def show_applications():
    # 🔍 ① 検索パラメータ取得
    filters = {
        "application_number": request.args.get("application_number"),
        "contract_number": request.args.get("contract_number"),
        "customer_name": request.args.get("customer_name"),
        "customer_name_kana": request.args.get("customer_name_kana"),
        "property_name": request.args.get("property_name"),
        "property_room_number": request.args.get("property_room_number"),
        "current_agency_name": request.args.get("current_agency_name"),
        "psp": request.args.get("psp"),
        "application_start": request.args.get("application_start"),
        "application_end": request.args.get("application_end"),
        "contract_start": request.args.get("contract_start"),
        "contract_end": request.args.get("contract_end")

    }

    # ✅ 検索条件があるかどうかを判定
    has_search = any(filters.values())

    # 表示件数とページ番号の取得
    limit = int(request.args.get("limit", 20))
    page = int(request.args.get("page", 1))
    offset = (page - 1) * limit

    results = []
    total = 0
    total_pages = 0

    if has_search:
        # 🧠 WHERE句・params構築
        like_keys = [
         "application_number", "contract_number", "customer_name",
         "customer_name_kana", "property_name", "property_room_number",
         "current_agency_name", "psp"
        ]
        range_keys = {
         "application_start": ("application_date", ">="),
         "application_end": ("application_date", "<="),
         "contract_start": ("contract_date", ">="),
         "contract_end": ("contract_date", "<=")
        }


        where_clauses = []
        params = {}
        # ① 通常のLIKE検索処理
        for key in like_keys:
            value = filters.get(key)
            if value:
                where_clauses.append(f"{key} LIKE %({key})s")
                params[key] = f"%{value}%"

        # ② 日付範囲検索処理
        for key, (column, operator) in range_keys.items():
            value = filters.get(key)
            if value:
                where_clauses.append(f"{column} {operator} %({key})s")
                params[key] = value

        # 🧾 SQL読み込み & WHERE句注入
        sql_template = load_sql("sql/applications/select_applicationlist.sql")
        where_sql = " AND " + " AND ".join(where_clauses) if where_clauses else ""
        sql = sql_template.replace("-- [WHERE]", where_sql)

        # LIMIT / OFFSET をSQLパラメータに追加
        params["limit"] = limit
        params["offset"] = offset

        # 🛠 DB接続 & 実行
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="mirai",
            db="miraihosho_system",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn:
            with conn.cursor() as cursor:
                count_sql = f"SELECT COUNT(*) as total FROM tr01_applicationlist WHERE 1=1 {where_sql}"
                cursor.execute(count_sql, params)
                total = cursor.fetchone()["total"]
                total_pages = (total + limit - 1) // limit

                cursor.execute(sql, params)
                results = cursor.fetchall()

    # 📦 テンプレートへ渡す
    return render_template(
        "applications/applicationslist.html",
        applications=results,
        user_id="admin",
        page=page,
        limit=limit,
        total_pages=total_pages,
        total=total,
        selected_limit=str(limit),
        base_url="/applications/applicationslist",
        has_search=has_search,
        filters=filters  # ← NEW: 検索済みかどうか
    )

@applications_bp.route("/applications/new", methods=["GET", "POST"])
def application_new():
    if request.method == "POST":
        # フォームから値を取得してDB登録処理
        # ...
        return redirect(url_for('applications.show_applications'))
    
    # GET時：空の form_data を渡して新規入力画面を表示
    return render_template(
        "applications/application_form.html",
        form_data=None,
        mode="create",
        submit_label="登録"
    )


@applications_bp.route("/applications/<application_number>", methods=["GET", "POST"])
def application_edit(application_number):
    # DBから該当申込を取得（主キーが application_number の想定）
    application = None
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="mirai",
        db="miraihosho_system",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

    with conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM tr01_applicationlist WHERE application_number = %s"
            cursor.execute(sql, (application_number,))
            application = cursor.fetchone()

    if request.method == "POST":
        # 更新処理
        # ...
        return redirect(url_for('applications.show_applications'))
    
    return render_template(
        "applications/application_form.html",
        form_data=application,
        mode="edit",
        submit_label="更新"
    )