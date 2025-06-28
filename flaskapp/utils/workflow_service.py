# flaskapp/utils/workflow_service.py

def get_permissions(status, user_role, user_id=None, requester_id=None):
    """
    現在のステータスとユーザー情報に基づき、
    各種操作の許可（Permission）を判定して返す。

    Args:
        status (str): 現在のレコードのステータス (例: '未登録', '承認待')
        user_role (str): 現在ログインしているユーザーの権限 (例: '管理者', '社員A', '一般')
        user_id (str, optional): 現在ログインしているユーザーの社員コード.
        requester_id (str, optional): この申請の申請者の社員コード.

    Returns:
        dict: 操作の許可状態を格納した辞書 (例: {'can_edit': True, 'can_assign': False})
    """

    # デフォルトの権限（すべて不許可）
    permissions = {
        'can_edit': False,
        'can_assign': False,
        'can_approve': False, # 承認・否認
        'can_send_back': False, # 差し戻し
        'can_confirm': False, # 確定
        'can_delete': False # 削除
    }

    # --- ステータスごとのルールをここに定義 ---

    if status in ['未登録', '登録済', '差し戻し']:
        # 編集: 全員可能
        permissions['can_edit'] = True
        # アサイン(承認依頼): 管理者と社員Aのみ可能
        if user_role in ['管理者', '社員A']:
            permissions['can_assign'] = True

    elif status == '承認待':
        # 編集: 申請者本人と管理者のみ可能
        # (注: user_id と requester_id を比較するには、呼び出し元でこれらの情報を渡す必要があります)
        if user_role == '管理者' or user_id == requester_id:
            permissions['can_edit'] = True
        
        # 承認/差し戻し: 管理者と社員Aのみ可能
        if user_role in ['管理者', '社員A']:
            permissions['can_approve'] = True
            permissions['can_send_back'] = True

    elif status == '確定':
        # 確定後は基本的にすべての操作を不可にする
        pass # 全てFalseのまま

    elif status == '削除済':
        # 削除後は何もできない
        pass

    # ... 将来的に他のルールもここに追加 ...

    return permissions

