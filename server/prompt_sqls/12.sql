select
    t1.ps_id
   ,REGEXP_REPLACE(t1.ps_name, '[\\n+\\r+\\t+\"+]',' ') as ps_name
   ,t1.dev_model_name
   ,t1.dev_pro_sn
   ,version1
   ,version2
   ,version3
   ,version4
   ,version5
from
(
    select
        t1.ps_id               as ps_id
       ,t1.ps_name             as ps_name
       ,t1.dev_model_name      as dev_model_name
       ,t1.dev_type_name       as dev_type_name
       ,t1.dev_pro_sn          as dev_pro_sn
       ,t1.dev_name            as dev_name
       ,t1.ps_location         as ps_location
       ,t1.ps_country_name     as ps_country_name
    from dwd_sungrow.dwd_pub_ps_dev_power_station_d  t1
    where pt=current_date()-1 and dev_type_name='储能逆变器'  and is_virtual_unit=0
) t1
join
(
    select
        t1.ps_id
       ,dev_model_name as dianchi_dev_model_name
       ,dev_pro_sn     as dianchi_dev_pro_sn
       ,dev_type_id
       , version1
       , version2
       , version3
       , version4
       , version5
    from dwd_sungrow.dwd_pub_ps_dev_power_station_d   t1
    where pt=current_date()-1  and is_virtual_unit=0
    and ( version1 in ('{0}') or  version2 in ('{0}') or version3 in ('{0}') or version4 in ('{0}') or version5 in ('{0}') )
) t2
on t1.ps_id=t2.ps_id
group by
    t1.ps_id
   ,REGEXP_REPLACE(t1.ps_name, '[\\n+\\r+\\t+\"+]',' ')
   ,t1.dev_model_name
   ,t1.dev_pro_sn
   ,version1
   ,version2
   ,version3
   ,version4
   ,version5