import os
import datetime
import json
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flaskapp.utils.db import get_db_connection
from flaskapp.common import constants
from flaskapp.services.logging_service import log_action

# Blueprintの定義
agency_sublist_bp = Blueprint(
    "agency_sublist", 
    __name__,
    template_folder='../../templates', # templatesフォルダのパスを指定
    static_folder='../../static' # staticフォルダのパスを指定
)

# ==============================================================================
# ヘルパー関数
# ==============================================================================
def get_agency_sub_fields():
    """ms04_agency_sublistテーブルのフォーム入力対象カラム名リストを返します"""
    return [
        'agency_master_code', 'sub_name', 'sub_name_kana', 
        'agencysub_postal_code', 'agencysub_prefecture', 'agencysub_city', 'agencysub_address', 
        'agencysub_tel', 'agencysub_fax', 'agencysub_mail',
        'application_count', 'contract_count', 'contract_rate',
        'approval_count', 'approval_rate', 'total_contracts',
        'overdue_count', 'overdue_rate', 'agency_sub_rank', 'rankdetails', 'remarks',
        'registration_date', 'registration_shain', 'update_date', 'update_shain',
        'registration_status', 'assignor_code', 'assignee_code'
    ]

def get_agency_sub_field_labels():
    """日本語の項目名リストを返します"""
    return {
        'agency_id': '代理店支店ID',
        'agency_master_code': '代理店本社コード',
        'agency_code': '代理店支店コード',
        'sub_code': '支店コード',
        'sub_name': '代理店支店名',
        'sub_name_kana': '代理店支店名カナ',
        'agencysub_postal_code': '郵便番号',
        'agencysub_prefecture': '都道府県',
        'agencysub_city': '市区町村',
        'agencysub_address': '番地',
        'agencysub_tel': '電話番号',
        'agencysub_fax': 'FAX',
        'agencysub_mail': 'メールアドレス',
        'application_count': '申込件数',
        'contract_count': '契約件数',
        'contract_rate': '契約率',
        'approval_count': '承認件数',
        'approval_rate': '承認率',
        'total_contracts': '契約総額',
        'overdue_count': '延滞件数',
        'overdue_rate': '延滞率',
        'agency_sub_rank': '代理店ランク',
        'rankdetails': 'ランク詳細',
        'remarks': '備考',
        'registration_date': '登録日',
        'registration_shain': '登録者',
        'update_date': '更新日',
        'update_shain': '更新者',
        'registration_status': '登録状況',
        'assignor_code': '担当者コード',
        'assignee_code': 'アサイン先コード'
    }

# ==============================================================================
# 代理店支店情報の一覧表示・検索機能
# ==============================================================================
@agency_sublist_bp.route("/masters/agency_sublist") # パスを元に戻しました
def show_agency_sublist():
    # 検索フィルターの受け取り
    filters = {
        "agency_code": request.args.get("agency_code", "").strip(),
        "agency_master_name": request.args.get("agency_master_name", "").strip(),
        "sub_name": request.args.get("sub_name", "").strip(),
        "agency_master_name_kana": request.args.get("agency_master_name_kana", "").strip(),
        "sub_name_kana": request.args.get("sub_name_kana", "").strip(),
        "address": request.args.get("address", "").strip(),
        "tel": request.args.get("tel", "").strip(),
        "registration_status": request.args.get("registration_status", "").strip(),
        "registration_date_from": request.args.get("registration_date_from", "").strip(),
        "registration_date_to": request.args.get("registration_date_to", "").strip(),
    }
    
    # ページネーションとソートの受け取り
    page = int(request.args.get("page", "1"))
    limit = int(request.args.get("limit", "20"))
    offset = (page - 1) * limit
    sort_by = request.args.get("sort_by")
    sort_order = request.args.get("sort_order")
    
    # ▼▼▼ 修正点 ▼▼▼ ソート対象に本社名などを追加
    allowed_sort_columns = [
        'agency_code', 'agency_master_name', 'sub_name', 
        'agency_master_name_kana', 'sub_name_kana', 
        'registration_status', 'registration_date'
    ]
    order_by_sql = "ORDER BY sub.agency_code ASC" # デフォルトのソート
    if sort_by in allowed_sort_columns and sort_order in ['asc', 'desc']:
        # JOINを考慮し、テーブル名を指定 (例: mas.agency_master_name)
        sort_column = f"mas.{sort_by}" if "master" in sort_by else f"sub.{sort_by}"
        order_by_sql = f"ORDER BY {sort_column} {sort_order.upper()}"

    conn = get_db_connection()
    if not conn:
        flash("データベースに接続できませんでした。", "danger")
        return render_template("masters/agency_sublist.html", sub_agencies=[], total=0, page=1, limit=limit, total_pages=0, filters=filters, registration_status=constants.registration_status_MAP)

    results = []
    total = 0
    try:
        sql_file_path = os.path.join(current_app.root_path, 'sql/agencies/select_agency_sublist.sql')
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            base_sql = f.read()

        # ▼▼▼ 修正点 ▼▼▼ WHERE句の組み立て（JOINを考慮）
        where_clauses = ["1=1"]
        params = {}
        if filters["agency_code"]:
            where_clauses.append("sub.agency_code LIKE %(agency_code)s")
            params['agency_code'] = f"%{filters['agency_code']}%"
        if filters["agency_master_name"]:
            where_clauses.append("mas.agency_master_name LIKE %(agency_master_name)s")
            params['agency_master_name'] = f"%{filters['agency_master_name']}%"
        if filters["agency_master_name_kana"]:
            where_clauses.append("mas.agency_master_name_kana LIKE %(agency_master_name_kana)s")
            params['agency_master_name_kana'] = f"%{filters['agency_master_name_kana']}%"
        if filters["sub_name"]:
            where_clauses.append("sub.sub_name LIKE %(sub_name)s")
            params['sub_name'] = f"%{filters['sub_name']}%"
        if filters["sub_name_kana"]:
            where_clauses.append("sub.sub_name_kana LIKE %(sub_name_kana)s")
            params['sub_name_kana'] = f"%{filters['sub_name_kana']}%"
        if filters["address"]:
            where_clauses.append("(sub.agencysub_prefecture LIKE %(address)s OR sub.agencysub_city LIKE %(address)s OR sub.agencysub_address LIKE %(address)s)")
            params['address'] = f"%{filters['address']}%"
        if filters["tel"]:
            where_clauses.append("sub.agencysub_tel LIKE %(tel)s")
            params['tel'] = f"%{filters['tel']}%"
        if filters["registration_status"]:
            where_clauses.append("sub.registration_status = %(registration_status)s")
            params['registration_status'] = filters['registration_status']
        if filters["registration_date_from"]:
            where_clauses.append("sub.registration_date >= %(registration_date_from)s")
            params['registration_date_from'] = filters['registration_date_from']
        if filters["registration_date_to"]:
            where_clauses.append("sub.registration_date <= %(registration_date_to)s")
            params['registration_date_to'] = filters['registration_date_to']

        where_sql = " AND ".join(where_clauses)
        
        # SQLのプレースホルダーを置換
        count_query_template = base_sql.replace("/*[LIMIT]*/", "").replace("/*[ORDER_BY]*/", "")
        count_query = count_query_template.replace("/*[WHERE]*/", f"WHERE {where_sql}")
        
        # COUNTクエリ用にSELECT句を変更
        # "FROM" の前の部分を "SELECT COUNT(*) as total" に置換
        count_sql = "SELECT COUNT(*) as total FROM" + count_query.split("FROM", 1)[1]


        with conn.cursor() as cursor:
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total'] or 0

            if total > 0:
                params_with_limit = params.copy()
                params_with_limit['limit'] = limit
                params_with_limit['offset'] = offset
                
                # 本体クエリの組み立て
                main_sql = base_sql.replace("/*[WHERE]*/", f"WHERE {where_sql}")
                main_sql = main_sql.replace("/*[ORDER_BY]*/", order_by_sql)
                main_sql = main_sql.replace("/*[LIMIT]*/", "LIMIT %(limit)s OFFSET %(offset)s")
                
                cursor.execute(main_sql, params_with_limit)
                results = cursor.fetchall()

    except Exception as e:
        flash(f"データ取得中にエラーが発生しました: {e}", "danger")
    finally:
        if conn: conn.close()
            
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    return render_template(
        "masters/agency_sublist.html", # パスを元に戻しました
        sub_agencies=results, # 変数名を変更
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        filters=filters,
        registration_status=constants.registration_status_MAP,
        sort_by=sort_by,
        sort_order=sort_order
    )

# ==============================================================================
# 代理店支店の新規登録
# ==============================================================================
@agency_sublist_bp.route("/masters/agency_sub/new", methods=["GET", "POST"])
def agency_sub_new():
    conn = get_db_connection()
    try:
        user_role = session.get('role', 0)
        button_config = {}
        # システム管理者、社員A, B の場合に「登録」ボタンを表示
        if user_role in [1, 3, 4]:
            button_config["show_instant_register"] = True

        if request.method == "POST":
            if not button_config.get("show_instant_register"):
                flash("この操作を行う権限がありません。", "danger")
                return redirect(url_for("agency_sublist.show_agency_sublist"))

            field_names = get_agency_sub_fields()
            form_data = {f: request.form.get(f, "").strip() for f in field_names}
            
            # 本社コードが選択されているかチェック
            agency_master_code = form_data.get("agency_master_code")
            if not agency_master_code:
                flash("親となる代理店本社を選択してください。", "error")
                # フォームデータを維持したまま再度フォームを表示
                return render_template("masters/agency_sub_form.html",
                                       mode="create",
                                       form_data=form_data,
                                       button_config=button_config)

            if not form_data.get("sub_name"):
                flash("代理店支店名を入力してください。", "error")
                return render_template("masters/agency_sub_form.html",
                                       mode="create",
                                       form_data=form_data,
                                       button_config=button_config)
            
            with conn.cursor() as cursor:
                # --- 支店コード(sub_code)の採番 ---
                cursor.execute(
                    "SELECT MAX(CAST(sub_code AS UNSIGNED)) as max_sub_code FROM ms04_agency_sublist WHERE agency_master_code = %s",
                    (agency_master_code,)
                )
                result = cursor.fetchone()
                max_sub_code = result['max_sub_code'] if result and result['max_sub_code'] is not None else 0
                new_sub_code = f"{int(max_sub_code) + 1:02d}" # 2桁のゼロ埋め

                # --- 代理店支店コード(agency_code)の生成 ---
                agency_code = f"{agency_master_code}{new_sub_code}"

                # 登録者情報などを追加
                form_data['registration_shain'] = session.get('shain_name', 'UNKNOWN')
                form_data['registration_date'] = datetime.datetime.now()
                form_data['registration_status'] = 1 # 登録時は「登録済」

                # --- データベースへのINSERT準備 ---
                # SQLインジェクションを防ぐため、カラム名をバッククォートで囲む
                all_fields = ['agency_code', 'sub_code'] + field_names
                columns_sql = ", ".join([f"`{col}`" for col in all_fields])
                placeholders_sql = ", ".join(["%s"] * len(all_fields))

                # 値のリストを作成
                values = [agency_code, new_sub_code]
                for f in field_names:
                    values.append(form_data.get(f) or None)

                # --- INSERT実行 ---
                sql_insert = f"INSERT INTO ms04_agency_sublist ({columns_sql}) VALUES ({placeholders_sql})"
                cursor.execute(sql_insert, values)
                
                # 登録されたデータのIDを取得
                new_agency_id = cursor.lastrowid
                conn.commit()
                
                log_action(
                    target_type=6,  # 6: 代理店支店マスタ (※要定義)
                    target_id=new_agency_id,
                    action_source=2, # 2: ユーザー操作
                    action_type=1,  # 1: 登録
                    action_details={'message': f'代理店支店 {agency_code} が新規登録されました。'}
                )

            flash(f"代理店支店コード {agency_code} で登録しました。", "success")
            # 登録したデータの編集画面にリダイレクト
            return redirect(url_for("agency_sublist.agency_sub_edit", agency_id=new_agency_id))
        
        # GETリクエスト（フォームの初期表示）
        form_data = {f: "" for f in get_agency_sub_fields()}
        # 代理店ランクの選択肢を生成 (masterlist.pyから流用)
        agency_rank_list = [{'value': key, 'label': value} for key, value in constants.AGENCY_RANK_MAP.items()]
        
        return render_template("masters/agency_sub_form.html",
                               mode="create",
                               form_data=form_data,
                               agency_rank_list=agency_rank_list,
                               button_config=button_config)
    finally:
        if conn and conn.open: conn.close()