-- run query 1 in stream 0 using template query82.tpl and seed 55585014
<<<<<<< HEAD
select  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 30 and 30+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-05-30' as date) and (cast('2002-05-30' as date) +  interval '60' day)
 and i_manufact_id in (437,129,727,663)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100
=======
select i_item_id
     , i_item_desc
     , i_current_price
from item,
     inventory,
     date_dim,
     store_sales
where i_current_price between 30 and 30 + 30
  and inv_item_sk = i_item_sk
  and d_date_sk = inv_date_sk
  and d_date between cast('2002-05-30' as date) and (cast('2002-05-30' as date) + interval '60' day)
  and i_manufact_id in (437, 129, 727, 663)
  and inv_quantity_on_hand between 100 and 500
  and ss_item_sk = i_item_sk
group by i_item_id, i_item_desc, i_current_price
order by i_item_id
limit 100
>>>>>>> c6e57f152b6cf3642e1037d16220c2d7462bcd36

-- end query 1 in stream 0 using template query82.tpl