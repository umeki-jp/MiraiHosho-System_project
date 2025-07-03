from flask import Flask, session # ★★★ 変更点 1: sessionをインポート ★★★
from flaskapp.routes.main import main_bp
from flaskapp.routes.auth import auth_bp
from flaskapp.routes.applications import applications_bp
from flaskapp.routes.root import root_bp
from flaskapp.routes.customerlist import customerlist_bp
from flaskapp.routes.api import api_bp
from .common import constants


def create_app():
    app = Flask(__name__)
    app.secret_key = "your-secret-key"
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(root_bp)
    app.register_blueprint(customerlist_bp)
    app.register_blueprint(api_bp)

    @app.context_processor
    def inject_status_maps():
        """テンプレートで使えるように定数を渡す"""
        return {
            'registration_status': constants.registration_status_MAP,
            'contract_status': constants.contract_status_MAP,
            'contract_version': constants.contract_version_MAP,
            'usage_purpose': constants.usage_purpose_map,
            'collection_method': constants.collection_method_map,
            'psp': constants.psp_map,
            'renewal_notice_method': constants.renewal_notice_method_map,
            'renewal_change_destination': constants.renewal_change_destination_map
        }

    # ★★★ 変更点 2: ログインユーザー情報を渡すコンテキストプロセッサーを追加 ★★★
    @app.context_processor
    def inject_user_info():
        """全てのテンプレートに共通のユーザー情報を渡す"""
        user_info = {
            'shain_name': session.get('shain_name', ''),
            'role': session.get('role', 0)  # ← roleも渡すように追加（未ログイン時は0）
        }
        return user_info

    return app