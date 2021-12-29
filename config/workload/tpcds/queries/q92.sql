-- run query 1 in stream 0 using template query92.tpl and seed 2031708268
<<<<<<< HEAD
select  
   sum(ws_ext_discount_amt)  as `Excess Discount Amount` 
from 
    web_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 269
and i_item_sk = ws_item_sk 
and d_date between '1998-03-18' and 
        (cast('1998-03-18' as date) + interval '90' day)
and d_date_sk = ws_sold_date_sk 
and ws_ext_discount_amt  
     > ( 
         SELECT 
            1.3 * avg(ws_ext_discount_amt) 
         FROM 
            web_sales 
           ,date_dim
         WHERE 
              ws_item_sk = i_item_sk 
          and d_date between '1998-03-18' and
                             (cast('1998-03-18' as date) + interval '90' day)
          and d_date_sk = ws_sold_date_sk 
      ) 
=======
select sum(ws_ext_discount_amt) as `Excess Discount Amount`
from web_sales
   , item
   , date_dim
where i_manufact_id = 269
  and i_item_sk = ws_item_sk
  and d_date between '1998-03-18' and
    (cast('1998-03-18' as date) + interval '90' day)
  and d_date_sk = ws_sold_date_sk
  and ws_ext_discount_amt
    > (
          SELECT 1.3 * avg(ws_ext_discount_amt)
          FROM web_sales
             , date_dim
          WHERE ws_item_sk = i_item_sk
            and d_date between '1998-03-18' and
              (cast('1998-03-18' as date) + interval '90' day)
            and d_date_sk = ws_sold_date_sk
      )
>>>>>>> c6e57f152b6cf3642e1037d16220c2d7462bcd36
order by sum(ws_ext_discount_amt)
limit 100

-- end query 1 in stream 0 using template query92.tpl
