SELECT
  au.user_id,
  au.shain_code,
  ms.shain_name,
  au.account_id,
  au.role,
  au.login_enabled,
  au.registration_date,
  au.registration_status
FROM
  ms_auth_user AS au
LEFT JOIN
  ms_shainlist AS ms ON au.shain_code = ms.shain_code
/*[WHERE]*/
/*[ORDER_BY]*/
/*[LIMIT]*/
;