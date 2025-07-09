SELECT
  customer_code,
  registration_status,
  name,
  name_kana,
  individual_birthdate,
  typeofcustomer,
  customer_rank,
  registration_date,
  -- 以下、検索機能のために追加 (画面には表示されない)
  individual_tel1,
  individual_tel2,
  corporate_tel1,
  corporate_tel2,
  individual_workplace
FROM
  ms01_customerlist