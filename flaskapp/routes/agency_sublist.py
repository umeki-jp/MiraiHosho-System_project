import os
import datetime
import json
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
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
# 代理店支店情報の一覧表示・検索機能
# ==============================================================================
@agency_sublist_bp.route("/sublist/agency_sublist")
def show_agency_sublist():
    # 検索フィルター
    filters = {
        "agency_code": request.args.get("agency_code", "").strip(),
        "sub_name": request.args.get("sub_name", "").strip(),
        "sub_name_kana": request.args.get("sub_name_kana", "").strip(),
        "address": request.args.get("address", "").strip(),
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

    allowed_sort_columns = ['agency_code', 'sub_name', 'sub_name_kana', 'registration_status', 'registration_date']
    order_by_sql = "ORDER BY agency_code ASC"
    if sort_by in allowed_sort_columns and sort_order in ['asc', 'desc']:
        order_by_sql = f"ORDER BY {sort_by} {sort_order.upper()}"

    conn = get_db_connection()
    if not conn:
        flash("データベースに接続できませんでした。", "danger")
        return render_template("sublist/agency_sublist.html", agencies=[], total=0, page=1, limit=limit, total_pages=0, filters=filters, registration_status=constants.registration_status_MAP)

    results = []
    total = 0
    try:
        where_clauses = ["1=1"]
        params = {}
        if filters["agency_code"]:
            where_clauses.append("agency_code LIKE %(agency_code)s")
            params['agency_code'] = f"%{filters['agency_code']}%"
        if filters["sub_name"]:
            where_clauses.append("sub_name LIKE %(sub_name)s")
            params['sub_name'] = f"%{filters['sub_name']}%"
        if filters["sub_name_kana"]:
            where_clauses.append("sub_name_kana LIKE %(sub_name_kana)s")
            params['sub_name_kana'] = f"%{filters['sub_name_kana']}%"
        if filters["address"]:
            # 住所は都道府県・市区町村・番地をまとめて検索
            where_clauses.append("(agencysub_prefecture LIKE %(address)s OR agencysub_city LIKE %(address)s OR agencysub_address LIKE %(address)s)")
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
            count_sql = f"SELECT COUNT(*) as total FROM ms04_agency_sublist WHERE {where_sql}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total'] or 0

            if total > 0:
                params_with_limit = params.copy()
                params_with_limit['limit'] = limit
                params_with_limit['offset'] = offset

                # TODO: SQLファイルを作成
                base_sql = "SELECT * FROM ms04_agency_sublist"
                sql = f"{base_sql} WHERE {where_sql} {order_by_sql} LIMIT %(limit)s OFFSET %(offset)s"

                cursor.execute(sql, params_with_limit)
                results = cursor.fetchall()

    except Exception as e:
        flash(f"データ取得中にエラーが発生しました: {e}", "danger")
    finally:
        if conn: conn.close()

    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    return render_template(
        "sublist/agency_sublist.html",
        agencies=results,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        filters=filters,
        registration_status=constants.registration_status_MAP,
        sort_by=sort_by,
        sort_order=sort_order
    )
