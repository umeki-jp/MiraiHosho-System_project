SELECT
  application_number,
  contract_number,
  contract_status,
  customer_name,
  property_name,
  property_room_number,
  current_agency_name,
  collection_method,
  psp,
  contract_start_date,
  cancellation_date

FROM
  tr01_applicationlist

WHERE
  1=1
-- [WHERE]

ORDER BY
  application_date DESC
LIMIT %(limit)s OFFSET %(offset)s;