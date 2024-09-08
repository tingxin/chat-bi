select
    t1.ps_key            as battery_ps_key
   ,t1.dev_pro_sn        as battery_dev_pro_sn
   ,t1.dev_model_name    as battery_dev_model_name
   ,t2.dev_pro_sn        as invert_dev_pro_sn
   ,t2.dev_model_name    as invert_dev_model_name
from
(
     select
        dev_uuid,ps_key,dev_type_name,dev_model_name,dev_pro_sn,up_uuid
     from dwd_sungrow.dwd_pub_ps_dev_power_station_d
     where pt=date_sub(current_date(), 1) and is_virtual_unit=0  and dev_type_id = 43
) t1
left join
(
    select
       dev_uuid,ps_key,dev_type_name,dev_model_name,dev_pro_sn,ps_name
    from dwd_sungrow.dwd_pub_ps_dev_power_station_d
    where pt=date_sub(current_date(), 1)  and is_virtual_unit=0 and dev_type_id = 14
) t2
on t1.up_uuid=t2.dev_uuid