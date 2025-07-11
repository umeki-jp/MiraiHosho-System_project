import datetime
import json
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flaskapp.utils.db import get_db_connection
from flaskapp.common import constants
from flaskapp.services.logging_service import log_action

agency_masterlist_bp = Blueprint("agency_masterlist", __name__)

# ==============================================================================
# ヘルパー関数
# ==============================================================================
def get_agency_master_fields():
    """ms03_agency_masterlistテーブルのフォーム入力対象カラム名リストを返します"""
    return [
        'agency_master_name', 'agency_master_name_kana', 'agency_master_postalcode', 'agency_master_prefecture', 
        'agency_master_city', 'agency_master_address', 'agency_master_tel', 'agency_master_fax', 'agency_master_mail', 
        'contract_version', 'contract_date', 'application_count','contract_count','contract_rate',
        'approval_count','approval_rate','total_contracts','overdue_count','overdue_rate',
        'agency_master_rank', 'agency_master_rankdetails', 'agency_master_remarks', 'registration_date',
        'registration_shain','update_date','update_shain','registration_status',
        'assignor_code', 'assignee_code'
    ]

def get_agency_master_field_labels():
    """日本語の項目名リストを返します"""
    return {
        'agency_master_code': '代理店本社コード',
        'agency_master_name': '代理店本社名',
        'agency_master_name_kana': '代理店本社名カナ',
        'agency_master_postalcode': '郵便番号',
        'agency_master_prefecture': '都道府県',
        'agency_master_city': '市区町村',
        'agency_master_address': '番地',
        'agency_master_tel': '電話番号',
        'agency_master_fax': 'FAX',
        'agency_master_mail': 'メールアドレス',
        'contract_version': '契約書ver',
        'contract_date': '契約日',
        'application_count': '申込件数',
        'contract_count': '契約件数',
        'contract_rate': '契約率',
        'approval_count': '承認件数',
        'approval_rate': '承認率',
        'total_contracts': '契約総額',
        'overdue_count': '延滞件数',
        'overdue_rate': '延滞率',
        'agency_master_rank': '代理店ランク',
        'agency_master_rankdetails': 'ランク詳細',
        'agency_master_remarks': '備考',
        'registration_date': '登録日',
        'registration_shain': '登録者',
        'update_date': '更新日',
        'update_shain': '更新者',
        'registration_status': '登録状況',
        'assignor_code': '担当者コード',
        'assignee_code': 'アサイン先コード'
    }

# ==============================================================================
# 代理店本社情報の一覧表示・検索機能
# ==============================================================================
@agency_masterlist_bp.route("/masters/agency_masterlist")
def show_agency_masterlist():
    # 検索フィルター
    filters = {
        "agency_master_code": request.args.get("agency_master_code", "").strip(),
        "agency_master_name": request.args.get("agency_master_name", "").strip(),
        "agency_master_name_kana": request.args.get("agency_master_name_kana", "").strip(),
        "address": request.args.get("address", "").strip(),
        "contract_version": request.args.get("contract_version", "").strip(),
        "registration_status": request.args.get("registration_status", "").strip(),
        "registration_date_from": request.args.get("registration_date_from", "").strip(),
        "registration_date_to": request.args.get("registration_date_to", "").strip(),
    }
    
    # ページネーションとソート
    page = int(request.args.get("page", "1"))
    limit = int(request.args.get("limit", "20"))
    offset = (page - 1) * limit
    sort_by = request.args.get("sort_by")
    sort_order = request.args.get("sort_order")
    
    allowed_sort_columns = ['agency_master_code', 'agency_master_name', 'agency_master_name_kana', 'contract_version', 'registration_status', 'registration_date']
    order_by_sql = "ORDER BY agency_master_code ASC"
    if sort_by in allowed_sort_columns and sort_order in ['asc', 'desc']:
        order_by_sql = f"ORDER BY {sort_by} {sort_order.upper()}"

    conn = get_db_connection()
    if not conn:
        flash("データベースに接続できませんでした。", "danger")
        return render_template("masters/agency_masterlist.html", agencies=[], total=0, page=1, limit=limit, total_pages=0, filters=filters, agreement_versions=constants.AGREEMENT_VERSION_MAP, registration_status=constants.registration_status_MAP)

    results = []
    total = 0
    try:
        where_clauses = ["1=1"]
        params = {}
        if filters["agency_master_code"]:
            where_clauses.append("agency_master_code LIKE %(agency_master_code)s")
            params['agency_master_code'] = f"%{filters['agency_master_code']}%"
        # 他のフィルター条件... (name, kana, address, etc.)
        if filters["address"]:
            where_clauses.append("(prefecture LIKE %(address)s OR city LIKE %(address)s OR address1 LIKE %(address)s OR address2 LIKE %(address)s)")
            params['address'] = f"%{filters['address']}%"
        if filters["contract_version"]:
            where_clauses.append("contract_version = %(contract_version)s")
            params['contract_version'] = filters['contract_version']
        # 他のフィルター条件... (status, date)
            
        where_sql = " AND ".join(where_clauses)
        
        with conn.cursor() as cursor:
            count_sql = f"SELECT COUNT(*) as total FROM ms03_agency_masterlist WHERE {where_sql}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total'] or 0

            if total > 0:
                params_with_limit = params.copy()
                params_with_limit['limit'] = limit
                params_with_limit['offset'] = offset
                
                # TODO: SQLファイルを作成
                base_sql = "SELECT * FROM ms03_agency_masterlist"
                sql = f"{base_sql} WHERE {where_sql} {order_by_sql} LIMIT %(limit)s OFFSET %(offset)s"
                
                cursor.execute(sql, params_with_limit)
                results = cursor.fetchall()

    except Exception as e:
        flash(f"データ取得中にエラーが発生しました: {e}", "danger")
    finally:
        if conn: conn.close()
            
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    return render_template(
        "masters/agency_masterlist.html",
        agencies=results,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        filters=filters,
        agreement_versions=constants.AGREEMENT_VERSION_MAP,
        registration_status=constants.registration_status_MAP,
        sort_by=sort_by,
        sort_order=sort_order
    )

# ==============================================================================
# 代理店本社の新規登録
# ==============================================================================
@agency_masterlist_bp.route("/masters/agency_master/new", methods=["GET", "POST"])
def agency_master_new():
    conn = get_db_connection()
    try:
        button_config = {'show_instant_register': True}

        if request.method == "POST":
            field_names = get_agency_master_fields()
            form_data = {f: request.form.get(f, "").strip() for f in field_names}
            
            if not form_data.get("agency_master_name"):
                flash("代理店本社名を入力してください。", "error")
                return render_template("masters/agency_master_form.html",
                                       mode="create",
                                       form_data=form_data,
                                       agreement_versions=constants.AGREEMENT_VERSION_MAP,
                                       button_config=button_config)
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(agency_master_code) as max_code FROM ms03_agency_masterlist WHERE agency_master_code REGEXP '^A[0-9]{5}$'")
                max_code = cursor.fetchone()['max_code']
                
                if max_code:
                    num_part = int(re.search(r'(\d+)$', max_code).group(1))
                    new_num = num_part + 1
                else:
                    new_num = 1
                agency_master_code = f"A{new_num:05d}"

                form_data['registration_shain'] = session.get('shain_name', 'UNKNOWN')
                form_data['registration_date'] = datetime.datetime.now()
                form_data['registration_status'] = 1

                values = [agency_master_code]
                for f in field_names:
                    values.append(form_data.get(f) or None)
                
                column_names = ", ".join(["agency_master_code"] + field_names)
                
                # ▼▼▼【この一行が抜けていました】▼▼▼
                sql_insert = f"INSERT INTO ms03_agency_masterlist ({column_names}) VALUES ({', '.join(['%s']*len(values))})"
                
                cursor.execute(sql_insert, values)
                conn.commit()

            flash(f"代理店本社コード {agency_master_code} で登録しました。", "success")
            return redirect(url_for("agency_masterlist.agency_master_edit", agency_master_code=agency_master_code))
        
        # GETリクエスト
        form_data = {f: "" for f in get_agency_master_fields()}
        return render_template("masters/agency_master_form.html",
                               mode="create",
                               form_data=form_data,
                               agreement_versions=constants.AGREEMENT_VERSION_MAP,
                               button_config=button_config)
    finally:
        if conn and conn.open: conn.close()

# ==============================================================================
# 代理店本社の編集・更新・削除機能
# ==============================================================================
@agency_masterlist_bp.route("/masters/agency_master/<agency_master_code>", methods=["GET", "POST"])
def agency_master_edit(agency_master_code):
    conn = get_db_connection()
    try:
        button_config = {"show_instant_update": True, "show_instant_delete": True}

        if request.method == "POST":
            action = request.form.get("action")
            field_names = get_agency_master_fields()

            if action == "update_instant":
                form_data = {f: request.form.get(f, "").strip() for f in field_names}
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM ms03_agency_masterlist WHERE agency_master_code = %s", (agency_master_code,))
                    before_data = cursor.fetchone()

                if not before_data:
                    flash("更新対象のデータが見つかりません。", "error")
                    return redirect(url_for('agency_masterlist.show_agency_masterlist'))

                changes = []
                field_labels = get_agency_master_field_labels()
                for field in field_names:
                    before_val = before_data.get(field, '')
                    after_val = form_data.get(field, '')
                    
                    # 両方の値を、比較しやすいように一度文字列に変換
                    before_str = str(before_val or '')
                    after_str = str(after_val or '')

                    # 'contract_version' の場合、特別に数値として比較する
                    if field == 'contract_version':
                        # 空文字やNoneを0として扱う
                        before_int = int(before_val or 0)
                        after_int = int(after_val or 0)
                        if before_int == after_int:
                            continue # 数値が同じなら、変更なしとして次のループへ

                    # 日付の場合、フォーマットを揃えてから比較する
                    elif field in ["registration_date", "update_date", "contract_date"]:
                        if isinstance(before_val, datetime.datetime):
                            before_str = before_val.strftime('%Y-%m-%dT%H:%M')
                        elif isinstance(before_val, datetime.date):
                            before_str = before_val.strftime('%Y-%m-%d')

                    # 契約書バージョンのようなMAPを使う項目は、表示名で比較
                    if field == 'contract_version':
                        before_str = constants.AGREEMENT_VERSION_MAP.get(int(before_val) if str(before_val).isdigit() else before_val, '未設定')
                        after_str = constants.AGREEMENT_VERSION_MAP.get(int(after_val) if str(after_val).isdigit() else after_val, '未設定')

                    # 比較前に日付フォーマットを統一する
                    if field in ["registration_date", "update_date", "contract_date"]:
                        if isinstance(before_val, datetime.datetime):
                            # datetime型は 'YYYY-MM-DDTHH:MM' 形式に
                            before_str = before_val.strftime('%Y-%m-%dT%H:%M')
                        elif isinstance(before_val, datetime.date):
                             # date型は 'YYYY-MM-DD' 形式に
                            before_str = before_val.strftime('%Y-%m-%d')
                    else:
                        before_str = str(before_val or '')

                    if before_str != after_str:
                        changes.append({"label": field_labels.get(field, field), "before": before_str, "after": after_str})

                if not changes:
                    flash("変更された項目がありません。", "info")
                    return redirect(url_for("agency_masterlist.agency_master_edit", agency_master_code=agency_master_code))
                
                return render_template("shared/update_confirm.html",
                                       changes=changes, form_data=form_data,
                                       submit_url=url_for('agency_masterlist.agency_master_edit', agency_master_code=agency_master_code),
                                       is_approval_flow=False, final_action_value="submit_update_instant")

            elif action == "submit_update_instant":
                form_data = {f: request.form.get(f, "").strip() for f in field_names}
                form_data['update_shain'] = session.get('shain_name', 'UNKNOWN')
                form_data['update_date'] = datetime.datetime.now()
                form_data['registration_status'] = 1

                values = [form_data.get(f) or None for f in field_names]
                values.append(agency_master_code)
                
                update_clause = ", ".join(f"{col} = %s" for col in field_names)
                sql = f"UPDATE ms03_agency_masterlist SET {update_clause} WHERE agency_master_code = %s"
                
                with conn.cursor() as cursor:
                    cursor.execute(sql, values)
                    conn.commit()
                return render_template("shared/action_done.html", action_label="更新")

            elif action == "delete_instant":
                deletable = True
                message = f"本当に代理店本社「{agency_master_code}」を削除しますか？"
                # (関連チェックロジックは将来のためにコメントアウト)
                return render_template("shared/delete_confirm.html", message=message, deletable=deletable,
                    submit_url=url_for('agency_masterlist.agency_master_delete_confirmed', agency_master_code=agency_master_code),
                    is_approval_flow=False, final_action_value="submit_delete_instant")

        # GETリクエスト (詳細表示)
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ms03_agency_masterlist WHERE agency_master_code = %s", (agency_master_code,))
            agency_data = cursor.fetchone()

        if not agency_data:
            flash("指定された代理店本社が見つかりませんでした。", "error")
            return redirect(url_for("agency_masterlist.show_agency_masterlist"))

        for field in ["registration_date", "update_date", "contract_date"]:
             if agency_data.get(field) and isinstance(agency_data.get(field), (datetime.date, datetime.datetime)):
                if isinstance(agency_data[field], datetime.datetime):
                    agency_data[field] = agency_data[field].strftime('%Y-%m-%dT%H:%M')
                else: # dateオブジェクトの場合
                    agency_data[field] = agency_data[field].strftime('%Y-%m-%d')
        
        for key, value in agency_data.items():
            if value is None:
                agency_data[key] = ''

        return render_template("masters/agency_master_form.html",
                               mode="edit",
                               form_data=agency_data,
                               button_config=button_config,
                               agreement_versions=constants.AGREEMENT_VERSION_MAP,
                               registration_status=constants.registration_status_MAP)
    finally:
        if conn and conn.open: conn.close()

# ==============================================================================
# 代理店本社の削除実行
# ==============================================================================
@agency_masterlist_bp.route("/masters/agency_master/delete/<agency_master_code>", methods=["POST"])
def agency_master_delete_confirmed(agency_master_code):
    conn = get_db_connection()
    try:
        if request.form.get("action") == "submit_delete_instant":
            with conn.cursor() as cursor:
                # ログ用にデータを取得してから削除
                cursor.execute("SELECT * FROM ms03_agency_masterlist WHERE agency_master_code = %s", (agency_master_code,))
                deleted_data = cursor.fetchone()
                cursor.execute("DELETE FROM ms03_agency_masterlist WHERE agency_master_code = %s", (agency_master_code,))
                conn.commit()

                if deleted_data:
                    # (ログ記録処理 ...)
                    pass
            return render_template("shared/action_done.html", action_label="削除")
    except Exception as e:
        flash(f"処理中にエラーが発生しました: {e}", "error")
    finally:
        if conn and conn.open: conn.close()
    return redirect(url_for('agency_masterlist.show_agency_masterlist'))