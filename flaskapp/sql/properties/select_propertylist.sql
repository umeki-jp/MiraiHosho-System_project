SELECT
  -- ▼ 一覧画面に表示するカラム
  property_code,
  property_name_kana,
  registration_status,
  registration_date,
  -- ▼ 検索機能のために裏側で必要なカラム
  property_name,
  property_prefecture,
  property_city,
  property_address
FROM
  ms02_propertylist