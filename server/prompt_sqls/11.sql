with battery2 as (
select
    t1.ps_id
   ,t1.ps_name
   ,t1.ps_key            as invert_ps_key
   ,t1.dev_pro_sn        as invert_dev_pro_sn
   ,t1.dev_model_name    as invert_dev_model_name
   ,t1.dev_uuid          as invert_dev_uuid
   ,t2.dev_uuid
   ,t2.dev_pro_sn        as battery_dev_pro_sn
   ,t2.dev_model_name    as battery_dev_model_name
   ,version1
   ,version2
   ,version3
   ,version4
   ,version5
from
(
     select
        dev_uuid,ps_key,dev_type_name,dev_model_name,dev_pro_sn,up_uuid,version1,version2,version3,version4,version5
     from dwd_sungrow.dwd_pub_ps_dev_power_station_d
     where pt=date_sub(current_date(), 1) and is_virtual_unit=0  and dev_type_id = 43
     and (version1 in ('SBRBCU-S_22011.01.06','SBRBCU-S_22011.01.07','SBRBCU-S_22011.01.09','SBRBCU-S_22011.01.0a','SBRBCU-S_22011.01.11','SBRBCU-S_22011.01.12','SBRBCU-S_22011.01.13','SBRBCU-S_22011.01.14','SBRBCU-S_22011.01.16','SBRBCU-S_22011.01.17','SBRBCU-S_22011.01.18','SBRBCU-S_22011.01.19','SBRBCU-S_22011.01.20','SBRBCU-S_22011.01.21')
    or version2 in ('SBRBCU-S_22011.01.06','SBRBCU-S_22011.01.07','SBRBCU-S_22011.01.09','SBRBCU-S_22011.01.0a','SBRBCU-S_22011.01.11','SBRBCU-S_22011.01.12','SBRBCU-S_22011.01.13','SBRBCU-S_22011.01.14','SBRBCU-S_22011.01.16','SBRBCU-S_22011.01.17','SBRBCU-S_22011.01.18','SBRBCU-S_22011.01.19','SBRBCU-S_22011.01.20','SBRBCU-S_22011.01.21')
    or version3 in ('SBRBCU-S_22011.01.06','SBRBCU-S_22011.01.07','SBRBCU-S_22011.01.09','SBRBCU-S_22011.01.0a','SBRBCU-S_22011.01.11','SBRBCU-S_22011.01.12','SBRBCU-S_22011.01.13','SBRBCU-S_22011.01.14','SBRBCU-S_22011.01.16','SBRBCU-S_22011.01.17','SBRBCU-S_22011.01.18','SBRBCU-S_22011.01.19','SBRBCU-S_22011.01.20','SBRBCU-S_22011.01.21')
    or version4 in ('SBRBCU-S_22011.01.06','SBRBCU-S_22011.01.07','SBRBCU-S_22011.01.09','SBRBCU-S_22011.01.0a','SBRBCU-S_22011.01.11','SBRBCU-S_22011.01.12','SBRBCU-S_22011.01.13','SBRBCU-S_22011.01.14','SBRBCU-S_22011.01.16','SBRBCU-S_22011.01.17','SBRBCU-S_22011.01.18','SBRBCU-S_22011.01.19','SBRBCU-S_22011.01.20','SBRBCU-S_22011.01.21')
    or version5 in ('SBRBCU-S_22011.01.06','SBRBCU-S_22011.01.07','SBRBCU-S_22011.01.09','SBRBCU-S_22011.01.0a','SBRBCU-S_22011.01.11','SBRBCU-S_22011.01.12','SBRBCU-S_22011.01.13','SBRBCU-S_22011.01.14','SBRBCU-S_22011.01.16','SBRBCU-S_22011.01.17','SBRBCU-S_22011.01.18','SBRBCU-S_22011.01.19','SBRBCU-S_22011.01.20','SBRBCU-S_22011.01.21'))
) t2
left join
(
    select
       dev_uuid,ps_key,dev_type_name,dev_model_name,dev_pro_sn,ps_name,ps_id
    from dwd_sungrow.dwd_pub_ps_dev_power_station_d
    where pt=date_sub(current_date(), 1)  and is_virtual_unit=0 and dev_type_id = 14
) t1
on t2.up_uuid=t1.dev_uuid
)