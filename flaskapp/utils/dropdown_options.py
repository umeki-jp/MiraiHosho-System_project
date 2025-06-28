# flaskapp/utils/dropdown_options.py

CUSTOMER_TYPES = [
    {"value": "個人", "label": "個人"},
    {"value": "法人", "label": "法人"},
]

GENDERS = [
    {"value": "男性", "label": "男性"},
    {"value": "女性", "label": "女性"},
    {"value": "その他", "label": "その他"},
]

ADDRESS_CATEGORIES = [
    {"value": "現住所", "label": "現住所"},
    {"value": "実家", "label": "実家"},
    {"value": "単身赴任先", "label": "単身赴任先"},
    {"value": "その他", "label": "その他"},
]

# 他のドロップダウン項目も同様に定義...