SELECT
  customer_code,
  name,
  name_kana,
  typeofcustomer,
  individual_birthDate,
  individual_workplace,
  customer_rank,
  registration_date,
  individual_tel1 AS contact_tel,
  individual_mail AS email
FROM ms01_customerlist
WHERE 1=1
-- [WHERE]
ORDER BY name
LIMIT %(limit)s OFFSET %(offset)s;