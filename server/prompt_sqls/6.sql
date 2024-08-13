SELECT DISTINCT
    org.user_account
    ,org.org_id
    ,REGEXP_REPLACE(org.org_name, '[\\n\\r\\t]',' ') AS org_name
    ,ps.ps_id
    ,REGEXP_REPLACE(ps.ps_name, '[\\n\\r\\t]',' ') AS ps_name
    ,dev.dev_model_name
    ,dev.dev_pro_sn
FROM (
    SELECT org_id, org_name, user_id, user_account
    FROM dwd_sungrow.dwd_pub_user_org_d 
    WHERE pt=CURRENT_DATE()-1 
    AND user_account='{0}' 
    AND is_master_org != -1
) org 
LEFT JOIN (
    SELECT
        org_id, sub_org_id
    FROM dwd_sungrow.dwd_org_sys_org_all_sub_org_d
    WHERE pt=CURRENT_DATE()-1
) sub ON org.org_id=sub.org_id
LEFT JOIN (
    SELECT
        ps_id, org_id, root_org_id, share_type, is_installer_ps_org
    FROM dwd_sungrow.dwd_ps_power_station_org_d
    WHERE pt=CURRENT_DATE()-1
) pso ON sub.sub_org_id = pso.org_id
LEFT JOIN (
    SELECT ps_id, dev_pro_sn, dev_model_name FROM dwd_sungrow.dwd_pub_ps_dev_power_station_d 
    WHERE pt=CURRENT_DATE()-1 AND dev_model_name IN ('{1}', '{2}')
) dev ON pso.ps_id = dev.ps_id
LEFT JOIN (
    SELECT ps_id,ps_name FROM dwd_sungrow.dwd_pub_ps_power_station_d
    WHERE pt=CURRENT_DATE()-1
) ps ON pso.ps_id = ps.ps_id
WHERE dev.ps_id IS NOT NULL AND ps.ps_id IS NOT NULL;

