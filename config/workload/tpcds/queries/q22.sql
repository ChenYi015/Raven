-- run query 1 in stream 0 using template query22.tpl and seed 1819994127
<<<<<<< HEAD
select  i_product_name
             ,i_brand
             ,i_class
             ,i_category
             ,avg(inv_quantity_on_hand) qoh
       from inventory
           ,date_dim
           ,item
           ,warehouse
       where inv_date_sk=d_date_sk
              and inv_item_sk=i_item_sk
              and inv_warehouse_sk = w_warehouse_sk
              and d_month_seq between 1212 and 1212 + 11
       group by rollup(i_product_name
                       ,i_brand
                       ,i_class
                       ,i_category)
=======
select i_product_name
     , i_brand
     , i_class
     , i_category
     , avg(inv_quantity_on_hand) qoh
from inventory
   , date_dim
   , item
   , warehouse
where inv_date_sk = d_date_sk
  and inv_item_sk = i_item_sk
  and inv_warehouse_sk = w_warehouse_sk
  and d_month_seq between 1212 and 1212 + 11
group by rollup (i_product_name
       , i_brand
       , i_class
       , i_category)
>>>>>>> c6e57f152b6cf3642e1037d16220c2d7462bcd36
order by qoh, i_product_name, i_brand, i_class, i_category
limit 100

-- end query 1 in stream 0 using template query22.tpl
