# ステータス
registration_status_MAP = {
    0: "未登録",
    1: "登録済",
    4: "確定",
    5: "削除済"
}

# ※以下のステータスは現在利用されていませんが、将来的に使用する可能性があります。
# 2: "承認待ち"
# 3: "差戻し"

# 契約状況ステータス
contract_status_MAP = {
    0: "未登録",
    1: "申込中",
    2: "審査承認",
    3: "契約中",
    4: "解約予定",
    5: "解約",
    6: "審査否決",
    7: "キャンセル",
    8: "不成立"
}

#　契約書バージョン
contract_version_MAP = {
    1: "初期",
    2: "2024.7.1版",
    3: "2025.2.1版"
}

# 利用用途
usage_purpose_map = {
    0: "選択なし",
    1: "居住用",
    2: "事業用",
    3: "駐車場"
}

# 集金方法
collection_method_map = {
    0: "口座振替",
    1: "クレジットカード",
    2: "コンビニ払い",
    3: "PayPal"
}


# 集金代行会社
psp_map = {
    0: "選択なし",
    1: "インサイト",
    2: "ジャックス",
    3: "クレジットカード"
}

# 更新案内方法
renewal_notice_method_map = {
    0: "選択なし",
    1: "リコーリース収納代行",
    2: "インサイト単発決済",
    3: "インサイト口座振替",
    4: "請求書"
}

# 宛先変更有無
renewal_change_destination_map = {
    0: "変更なし",
    1: "変更あり"
}

# 認証用アカウントの権限
role_map = {
    0: "未設定",
    1: "システム管理者",
    2: "閲覧のみ",
    3: "社員A",
    4: "社員B"
}

# 顧客ランクの定義
CUSTOMER_RANK_MAP = {
    0: "一般",
    1: "優良",
    2: "延滞歴あり",
    3: "準ブラック",
    4: "ブラック"
}

# 顧客ランクの定義　逆引き用
CUSTOMER_RANK_LIST = [
    {'value': 0, 'label': '一般'},
    {'value': 1, 'label': '優良'},
    {'value': 2, 'label': '延滞歴あり'},
    {'value': 3, 'label': '準ブラック'},
    {'value': 4, 'label': 'ブラック'}
]

# --- 対応履歴用定数 ---

# 対象タイプ (何に対するログか)
TARGET_TYPE_MAP = {
    0: '未設定',
    1: '契約',
    2: '代理店',
    3: '顧客リスト',
    4: '物件リスト',
    5: '代理店本社リスト',
    6: '代理店リスト',
    7: 'プランリスト',
    8: '仲介リスト',
    9: '緊急・入居者リスト',
    10: '社員リスト',
    11: '認証用アカウント',
}

# 対象cdごとの名称表示用（残りも追加必要）
TARGET_NAME_MAPPING = {
    1: {'table': 'tr01_applicationlistapplicationlist', 'id_column': 'application_number', 'name_column': 'customer_name'},
    2: {'table': 'ms04_agency_sublist', 'id_column': 'agency_code', 'name_column': 'agency_master_name'},
    3: {'table': 'ms01_customerlist', 'id_column': 'customer_code', 'name_column': 'name'},
    4: {'table': 'ms02_propertylist', 'id_column': 'property_code', 'name_column': 'property_name'},
    5: {'table': 'ms03_agency_masterlist', 'id_column': 'agency_master_code', 'name_column': 'agency_master_name'},
    10: {'table': 'ms_shainlist', 'id_column': 'shain_code', 'name_column': 'shain_name'}
}

# 操作の発生源 (どうやって行われたか)
ACTION_SOURCE_MAP = {
    0: '未設定',
    1: '手動',
    2: 'ユーザー操作',
    3: 'バッチ'
}

# 操作の種類 (何をしたか)
ACTION_TYPE_MAP = {
    0: '未設定',
    1: '登録',
    2: '更新',
    3: '削除',
    4: '確定'
}

# --- 代理店 ---

# 契約書バージョン
AGREEMENT_VERSION_MAP = {
    0: '未締結',
    1: '2024年7月1日版'
    # 必要に応じて今後追加
}