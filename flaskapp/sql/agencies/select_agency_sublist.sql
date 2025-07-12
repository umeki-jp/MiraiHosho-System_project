SELECT
    sub.agency_id,
    sub.agency_code,
    sub.sub_name,
    sub.sub_name_kana,
    sub.agencysub_prefecture,
    sub.agencysub_city,
    sub.agencysub_address,
    sub.agencysub_tel,
    sub.registration_status,
    sub.registration_date,
    mas.agency_master_name,
    mas.agency_master_name_kana
FROM
    ms04_agency_sublist AS sub
LEFT JOIN
    ms03_agency_masterlist AS mas ON sub.agency_master_code = mas.agency_master_code
/*[WHERE]*/
/*[ORDER_BY]*/
/*[LIMIT]*/
;