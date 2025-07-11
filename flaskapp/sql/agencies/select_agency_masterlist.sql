SELECT
  -- ▼ 一覧画面に表示するカラム
  agency_master_code,
  agency_master_name,
  agency_master_name_kana,
  contract_version,
  registration_status,
  registration_date,

  -- ▼ 検索機能のために裏側で必要なカラム
  prefecture,
  city,
  agency_master_address
FROM
  ms03_agency_masterlist