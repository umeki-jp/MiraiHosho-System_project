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
        if filters["agency_master_name"]:
            where_clauses.append("agency_master_name LIKE %(agency_master_name)s")
            params['agency_master_name'] = f"%{filters['agency_master_name']}%"
        if filters["agency_master_name_kana"]:
            where_clauses.append("agency_master_name_kana LIKE %(agency_master_name_kana)s")
            params['agency_master_name_kana'] = f"%{filters['agency_master_name_kana']}%"
        if filters["address"]:
            # 住所は都道府県・市区町村・番地をまとめて検索
            where_clauses.append("(agency_master_prefecture LIKE %(address)s OR agency_master_city LIKE %(address)s OR agency_master_address LIKE %(address)s)")
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
        user_role = session.get('role', 0)
        button_config = {}
        # システム管理者、社員A, B の場合に「登録」ボタンを表示
        if user_role in [1, 3, 4]:
            button_config["show_instant_register"] = True

        if request.method == "POST":
            if not button_config.get("show_instant_register"):
                flash("この操作を行う権限がありません。", "danger")
                return redirect(url_for("agency_masterlist.show_agency_masterlist"))
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
                
                log_action(
                    target_type=5,  # 5: 代理店本社マスタ (※要定義)
                    target_id=agency_master_code,
                    action_source=2, # 2: ユーザー操作
                    action_type=1,  # 1: 登録
                    action_details={'message': f'代理店本社 {agency_master_code} が新規登録されました。'}
                )

            flash(f"代理店本社コード {agency_master_code} で登録しました。", "success")
            return redirect(url_for("agency_masterlist.agency_master_edit", agency_master_code=agency_master_code))
        
        # GETリクエスト
        form_data = {f: "" for f in get_agency_master_fields()}
        # 代理店ランクの選択肢を生成
        agency_rank_list = [{'value': key, 'label': value} for key, value in constants.AGENCY_RANK_MAP.items()]
        
        return render_template("masters/agency_master_form.html",
                               mode="create",
                               form_data=form_data,
                               agreement_versions=constants.AGREEMENT_VERSION_MAP,
                               agency_rank_list=agency_rank_list,  # 追加
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
        user_role = session.get('role', 0) # デフォルトは0 (権限なし)

        # デフォルトでは全ての操作ボタンを非表示（閲覧のみ）
        button_config = {
            "show_instant_update": False,
            "show_instant_delete": False,
        }

        # ロールに基づいてボタンの表示を決定 (customerlist.pyに準拠)
        if user_role in [1, 3]:  # 1:システム管理者, 3:社員A
            button_config["show_instant_update"] = True
            button_config["show_instant_delete"] = True
        elif user_role == 4:  # 4:社員B
            button_config["show_instant_update"] = True

        if request.method == "POST":
            action = request.form.get("action")
            if action in ["update_instant", "submit_update_instant"] and not button_config.get("show_instant_update"):
                flash("この操作を行う権限がありません。", "danger")
                return redirect(url_for("agency_masterlist.show_agency_masterlist"))
            if action in ["delete_instant"] and not button_config.get("show_instant_delete"):
                flash("この操作を行う権限がありません。", "danger")
                return redirect(url_for("agency_masterlist.show_agency_masterlist"))
            field_names = get_agency_master_fields()

            if action == "update_instant":
                # フォームから送信されたデータを取得
                form_data = {f: request.form.get(f, "").strip() for f in field_names}
                
                # 変更前のデータをDBから取得
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM ms03_agency_masterlist WHERE agency_master_code = %s", (agency_master_code,))
                    before_data = cursor.fetchone()

                # データが存在しない場合はエラー
                if not before_data:
                    flash("更新対象のデータが見つかりません。", "error")
                    return redirect(url_for('agency_masterlist.show_agency_masterlist'))

                # 変更点を格納するリストを初期化
                changes = []
                field_labels = get_agency_master_field_labels()

                # 全てのフィールドをループして変更点をチェック
                for field in field_names:
                    before_val = before_data.get(field)
                    after_val = form_data.get(field, "")

                    # 比較用の文字列を初期化
                    before_str = ""
                    after_str = str(after_val or '')

                    # --- 1. フィールドの種類に応じて、比較用の文字列を整形 ---
                    # [契約日] は日付(YYYY-MM-DD)の部分だけを比較
                    if field == 'contract_date':
                        if isinstance(before_val, (datetime.date, datetime.datetime)):
                            before_str = before_val.strftime('%Y-%m-%d')
                    
                    # [登録日/更新日] は日時(YYYY-MM-DDTHH:MM)で比較
                    elif field in ["registration_date", "update_date"]:
                        if isinstance(before_val, datetime.datetime):
                            before_str = before_val.strftime('%Y-%m-%dT%H:%M')

                    # [契約書ver] は表示名で比較
                    elif field == 'contract_version':
                        before_str = constants.AGREEMENT_VERSION_MAP.get(int(before_val) if str(before_val).isdigit() else before_val, '未設定')
                        after_str = constants.AGREEMENT_VERSION_MAP.get(int(after_val) if str(after_val).isdigit() else after_val, '未設定')

                    # ▼▼▼【ここから追加】▼▼▼
                    # [代理店ランク] は表示名で比較
                    elif field == 'agency_master_rank':
                        before_str = constants.AGENCY_RANK_MAP.get(int(before_val) if str(before_val).isdigit() else before_val, '未設定')
                        after_str = constants.AGENCY_RANK_MAP.get(int(after_val) if str(after_val).isdigit() else after_val, '未設定')
                    # ▲▲▲【ここまで追加】▲▲▲

                    # [上記以外] のフィールドは単純な文字列として比較
                    else:
                        before_str = str(before_val or '')

                    # --- 2. 整形後の文字列を比較して、異なれば変更リストに追加 ---
                    if before_str != after_str:
                        changes.append({
                            "label": field_labels.get(field, field), 
                            "before": before_str, 
                            "after": after_str
                        })

                # 変更が一つもなければ、メッセージを表示して編集画面に戻る
                if not changes:
                    flash("変更された項目がありません。", "info")
                    return redirect(url_for("agency_masterlist.agency_master_edit", agency_master_code=agency_master_code))
                
                # 変更点があれば、確認画面を表示
                return render_template("shared/update_confirm.html",
                                       changes=changes, 
                                       form_data=form_data,
                                       changes_json=json.dumps(changes), 
                                       submit_url=url_for('agency_masterlist.agency_master_edit', agency_master_code=agency_master_code),
                                       is_approval_flow=False, 
                                       final_action_value="submit_update_instant")

            elif action == "submit_update_instant":
                form_data = {f: request.form.get(f, "").strip() for f in field_names}
                form_data['update_shain'] = session.get('shain_name', 'UNKNOWN')
                form_data['update_date'] = datetime.datetime.now()
                form_data['registration_status'] = 1

                # フォームから来た日付文字列(YYYY-MM-DD)をDB保存形式に整える
                # contract_dateが空文字やNoneでなく、有効な日付形式の場合のみ変換を試みる
                contract_date_str = form_data.get("contract_date")
                if contract_date_str:
                    try:
                        # YYYY-MM-DD形式の文字列をdatetimeオブジェクトに変換
                        date_obj = datetime.datetime.strptime(contract_date_str, '%Y-%m-%d')
                        # DB保存用に再度 YYYY-MM-DD 形式の文字列にする（DATE型カラムの場合）
                        form_data["contract_date"] = date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        # 無効な日付形式の場合はNone（NULL）として扱う
                        form_data["contract_date"] = None
                else:
                    # 入力が空の場合もNone（NULL）をセット
                    form_data["contract_date"] = None

                # 登録日・更新日はdatetime-localからの値を変換する
                for field in ["registration_date", "update_date"]:
                    date_str = form_data.get(field)
                    if date_str and isinstance(date_str, str): # 文字列の場合のみ変換
                        try:
                            form_data[field] = datetime.datetime.strptime(date_str.replace('T', ' '), '%Y-%m-%d %H:%M')
                        except (ValueError, AttributeError):
                            form_data[field] = None # 変換失敗時はNone

                values = [form_data.get(f) or None for f in field_names]
                values.append(agency_master_code)
                
                update_clause = ", ".join(f"{col} = %s" for col in field_names)
                sql = f"UPDATE ms03_agency_masterlist SET {update_clause} WHERE agency_master_code = %s"
                
                with conn.cursor() as cursor:
                    cursor.execute(sql, values)
                    conn.commit()
                    
                log_action(
                        target_type=5,  # 5: 代理店本社マスタ (※要定義)
                        target_id=agency_master_code,
                        action_source=2, # 2: ユーザー操作
                        action_type=2,  # 2: 更新
                        action_details=json.loads(request.form.get('changes_json', '[]')) # 確認画面から変更内容を受け取る
                    )
                
                return render_template("shared/action_done.html", action_label="更新")

            elif action == "delete_instant":
                deletable = True
                message = f"本当に代理店本社「{agency_master_code}」を削除しますか？"
                # --- 関連データチェック（将来有効化） ---
                # 将来、代理店支店テーブルなどができた場合、以下のコメントアウトを解除して使用します。
                # with conn.cursor() as cursor:
                #     # 例: ms04_agency_sublist に、この本社コードを持つ支店がないかチェック
                #     cursor.execute("SELECT COUNT(*) as count FROM ms04_agency_sublist WHERE agency_master_code = %s", (agency_master_code,))
                #     related_count = cursor.fetchone()['count']
                #
                #     if related_count > 0:
                #         deletable = False
                #         message = f"この代理店本社（{agency_master_code}）には {related_count} 件の支店が紐づいているため、削除できません。"
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

        # 日付/日時フィールドをHTMLのinputが解釈できる形式に変換
        date_fields_to_format = {
            "contract_date": '%Y-%m-%d',         # <input type="date"> 用
            "registration_date": '%Y-%m-%dT%H:%M', # <input type="datetime-local"> 用
            "update_date": '%Y-%m-%dT%H:%M'      # <input type="datetime-local"> 用
        }
        for field, fmt in date_fields_to_format.items():
            if agency_data.get(field) and isinstance(agency_data.get(field), (datetime.date, datetime.datetime)):
                agency_data[field] = agency_data[field].strftime(fmt)
        
        # None の値を空文字に変換（テンプレートでのエラー防止）
        for key, value in agency_data.items():
            if value is None:
                agency_data[key] = ''

        agency_rank_list = [{'value': key, 'label': value} for key, value in constants.AGENCY_RANK_MAP.items()]

        return render_template("masters/agency_master_form.html",
                               mode="edit",
                               form_data=agency_data,
                               button_config=button_config,
                               agreement_versions=constants.AGREEMENT_VERSION_MAP,
                               registration_status=constants.registration_status_MAP,
                               agency_rank_list=agency_rank_list)
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

                for key, value in deleted_data.items():
                    if isinstance(value, (datetime.date, datetime.datetime)):
                            deleted_data[key] = value.isoformat()
                    
                    log_action(
                        target_type=5,  # 5: 代理店本社マスタ (※要定義)
                        target_id=agency_master_code,
                        action_source=2, # 2: ユーザー操作
                        action_type=3,  # 3: 削除
                        action_details={'deleted_data': deleted_data}
                    )
                    
            return render_template("shared/action_done.html", action_label="削除")
    except Exception as e:
        flash(f"処理中にエラーが発生しました: {e}", "error")
    finally:
        if conn and conn.open: conn.close()
    return redirect(url_for('agency_masterlist.show_agency_masterlist'))