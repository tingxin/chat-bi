SELECT
     ps.user_id
    ,ps.user_account
    ,ps.org_id
    ,ps.org_name
    ,ps.ps_id
    ,conn.ps_name
    ,conn.dev_pro_sn
    ,conn.dev_model_name
    ,sim.failure_date
    ,sim.sim_no
    ,sim.sim_iccid
    ,sim.sim_status
FROM (
    SELECT
        suo.org_id, org_name, user_id, user_account,pso.ps_id
    FROM (
        SELECT
            org_id, org_name, user_id, user_account
        FROM dwd_sungrow.dwd_pub_user_org_d
        WHERE pt=date_sub(current_date(), 1)
        AND is_master_org!=-1 AND user_account in ('{0}')
        GROUP BY org_id, org_name, user_id, user_account
    ) suo
    LEFT JOIN (
        SELECT
            org_id, sub_org_id
        FROM dwd_sungrow.dwd_org_sys_org_all_sub_org_d
        WHERE pt=date_sub(current_date(), 1)
    ) sub ON suo.org_id=sub.org_id
    JOIN (
        SELECT
            ps_id, org_id, root_org_id, share_type, is_installer_ps_org
        FROM dwd_sungrow.dwd_ps_power_station_org_d
        WHERE pt=date_sub(current_date(), 1)
    ) pso ON sub.sub_org_id = pso.org_id
    WHERE sub.org_id IS NOT NULL AND pso.ps_id IS NOT NULL
    GROUP BY suo.org_id, org_name, user_id, user_account,pso.ps_id
) ps
LEFT JOIN (
    SELECT ps_id,ps_name, dev_pro_sn, dev_model_name FROM dwd_sungrow.dwd_pub_ps_dev_power_station_d
    WHERE pt=date_sub(current_date(), 1) AND dev_type_id IN (9, 22)
) conn ON ps.ps_id = conn.ps_id
LEFT JOIN (
    SELECT dev_sn, failure_date, sim_no, sim_iccid, sim_status FROM dwd_sungrow.dwd_sn_dev_sim_d
    WHERE pt=date_sub(current_date(), 1)
) sim ON conn.dev_pro_sn = sim.dev_sn
WHERE conn.ps_id IS NOT NULL AND sim.dev_sn IS NOT NULL
;