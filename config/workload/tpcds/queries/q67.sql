-- run query 1 in stream 0 using template query67.tpl and seed 1819994127
<<<<<<< HEAD
select  *
from (select i_category
            ,i_class
            ,i_brand
            ,i_product_name
            ,d_year
            ,d_qoy
            ,d_moy
            ,s_store_id
            ,sumsales
            ,rank() over (partition by i_category order by sumsales desc) rk
      from (select i_category
                  ,i_class
                  ,i_brand
                  ,i_product_name
                  ,d_year
                  ,d_qoy
                  ,d_moy
                  ,s_store_id
                  ,sum(coalesce(ss_sales_price*ss_quantity,0)) sumsales
            from store_sales
                ,date_dim
                ,store
                ,item
       where  ss_sold_date_sk=d_date_sk
          and ss_item_sk=i_item_sk
          and ss_store_sk = s_store_sk
          and d_month_seq between 1212 and 1212+11
       group by  rollup(i_category, i_class, i_brand, i_product_name, d_year, d_qoy, d_moy,s_store_id))dw1) dw2
where rk <= 100
order by i_category
        ,i_class
        ,i_brand
        ,i_product_name
        ,d_year
        ,d_qoy
        ,d_moy
        ,s_store_id
        ,sumsales
        ,rk
=======
select *
from (select i_category
           , i_class
           , i_brand
           , i_product_name
           , d_year
           , d_qoy
           , d_moy
           , s_store_id
           , sumsales
           , rank() over (partition by i_category order by sumsales desc) rk
      from (select i_category
                 , i_class
                 , i_brand
                 , i_product_name
                 , d_year
                 , d_qoy
                 , d_moy
                 , s_store_id
                 , sum(coalesce(ss_sales_price * ss_quantity, 0)) sumsales
            from store_sales
               , date_dim
               , store
               , item
            where ss_sold_date_sk = d_date_sk
              and ss_item_sk = i_item_sk
              and ss_store_sk = s_store_sk
              and d_month_seq between 1212 and 1212 + 11
            group by rollup (i_category, i_class, i_brand, i_product_name, d_year, d_qoy, d_moy, s_store_id)) dw1) dw2
where rk <= 100
order by i_category
       , i_class
       , i_brand
       , i_product_name
       , d_year
       , d_qoy
       , d_moy
       , s_store_id
       , sumsales
       , rk
>>>>>>> c6e57f152b6cf3642e1037d16220c2d7462bcd36
limit 100

-- end query 1 in stream 0 using template query67.tpl
