-- run query 1 in stream 0 using template query32.tpl and seed 2031708268
<<<<<<< HEAD
select  sum(cs_ext_discount_amt)  as `excess discount amount`
from 
   catalog_sales 
   ,item 
   ,date_dim
where
i_manufact_id = 269
and i_item_sk = cs_item_sk 
and d_date between '1998-03-18' and 
        (cast('1998-03-18' as date) + interval '90' day)
and d_date_sk = cs_sold_date_sk 
and cs_ext_discount_amt  
     > ( 
         select 
            1.3 * avg(cs_ext_discount_amt) 
         from 
            catalog_sales 
           ,date_dim
         where 
              cs_item_sk = i_item_sk 
          and d_date between '1998-03-18' and
                             (cast('1998-03-18' as date) + interval '90' day)
          and d_date_sk = cs_sold_date_sk 
      ) 
=======
select sum(cs_ext_discount_amt) as `excess discount amount`
from catalog_sales
   , item
   , date_dim
where i_manufact_id = 269
  and i_item_sk = cs_item_sk
  and d_date between '1998-03-18' and
    (cast('1998-03-18' as date) + interval '90' day)
  and d_date_sk = cs_sold_date_sk
  and cs_ext_discount_amt
    > (
          select 1.3 * avg(cs_ext_discount_amt)
          from catalog_sales
             , date_dim
          where cs_item_sk = i_item_sk
            and d_date between '1998-03-18' and
              (cast('1998-03-18' as date) + interval '90' day)
            and d_date_sk = cs_sold_date_sk
      )
>>>>>>> c6e57f152b6cf3642e1037d16220c2d7462bcd36
limit 100

-- end query 1 in stream 0 using template query32.tpl
