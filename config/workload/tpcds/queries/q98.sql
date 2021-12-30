-- run query 1 in stream 0 using template query98.tpl and seed 345591136
<<<<<<< HEAD
select i_item_desc 
      ,i_category 
      ,i_class 
      ,i_current_price
      ,sum(ss_ext_sales_price) as itemrevenue 
      ,sum(ss_ext_sales_price)*100/sum(sum(ss_ext_sales_price)) over
          (partition by i_class) as revenueratio
from	
	store_sales
    	,item 
    	,date_dim
where 
	ss_item_sk = i_item_sk 
  	and i_category in ('Jewelry', 'Sports', 'Books')
  	and ss_sold_date_sk = d_date_sk
	and d_date between cast('2001-01-12' as date) 
				and (cast('2001-01-12' as date) + interval '30' day)
group by 
	i_item_id
        ,i_item_desc 
        ,i_category
        ,i_class
        ,i_current_price
order by 
	i_category
        ,i_class
        ,i_item_id
        ,i_item_desc
        ,revenueratio
=======
select i_item_desc
     , i_category
     , i_class
     , i_current_price
     , sum(ss_ext_sales_price) as itemrevenue
     , sum(ss_ext_sales_price) * 100 / sum(sum(ss_ext_sales_price)) over
    (partition by i_class)     as revenueratio
from store_sales
   , item
   , date_dim
where ss_item_sk = i_item_sk
  and i_category in ('Jewelry', 'Sports', 'Books')
  and ss_sold_date_sk = d_date_sk
  and d_date between cast('2001-01-12' as date)
    and (cast('2001-01-12' as date) + interval '30' day)
group by i_item_id
       , i_item_desc
       , i_category
       , i_class
       , i_current_price
order by i_category
       , i_class
       , i_item_id
       , i_item_desc
       , revenueratio
>>>>>>> c6e57f152b6cf3642e1037d16220c2d7462bcd36

-- end query 1 in stream 0 using template query98.tpl