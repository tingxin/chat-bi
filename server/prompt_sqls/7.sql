SELECT 
    ps.org_id
    ,REGEXP_REPLACE(ps.org_name, '[\\n\\r\\t]',' ') as org_name
    ,ps.user_id
    ,ps.user_account
    ,ps.ps_id
    ,ps.ps_name
    ,ps.recore_create_time
    ,ps.ps_country_name
    ,ps.ps_location
    ,ps.total_installed_power
    ,ps.nibianqi_cnt
    ,ps.chunengnibianqi_cnt
    ,ps.tongxunshebei_cnt
    ,dev_cnt
FROM (
    SELECT DISTINCT
        suo.org_id, org_name, user_id, user_account, dev.ps_id
        , dev.ps_name, recore_create_time,ps_country_name,ps_location
        , SUM(total_installed_power)   AS total_installed_power
        , SUM(IF(dev_type_id='1',1,0)) AS nibianqi_cnt
        , SUM(IF(dev_type_id='14',1,0)) AS chunengnibianqi_cnt
        , SUM(IF(dev_type_id in ('9','22'),1,0)) AS tongxunshebei_cnt
        , count(1) as dev_cnt
    FROM (
        SELECT 
            org_id, org_name, user_id, user_account
        FROM dwd_sungrow.dwd_pub_user_org_d 
        WHERE pt=CURRENT_DATE()-1 
        AND is_master_org!=-1 AND user_account='{0}'
        GROUP BY org_id, org_name, user_id, user_account
    ) suo
    LEFT JOIN (
        SELECT 
            org_id, sub_org_id
        FROM dwd_sungrow.dwd_org_sys_org_all_sub_org_d 
        WHERE pt=CURRENT_DATE()-1
    ) sub ON suo.org_id=sub.org_id
    JOIN (
        SELECT
            ps_id, org_id, root_org_id, share_type, is_installer_ps_org
        FROM dwd_sungrow.dwd_ps_power_station_org_d
        WHERE pt=CURRENT_DATE()-1
    ) pso ON sub.sub_org_id = pso.org_id
    LEFT JOIN (
        SELECT 
            ps_id, ps_name, recore_create_time,dev_type_id,ps_country_name,ps_location
            , total_installed_power
        FROM dwd_sungrow.dwd_pub_ps_dev_power_station_d WHERE pt=CURRENT_DATE()-1
    ) dev ON pso.ps_id = dev.ps_id
    WHERE sub.org_id IS NOT NULL AND dev.ps_id IS NOT NULL
    GROUP BY suo.org_id, org_name, user_id, user_account
        , dev.ps_id, dev.ps_name, recore_create_time,ps_country_name,ps_location
) ps;