#!/usr/bin/python3

import sys
import random
import atexit
import signal
import subprocess

from threading import Thread
from threading import Lock
from time import sleep
import time

ch_queries = [
"""
-- Q01
select 
    ol_number, sum(ol_quantity) as sum_qty,
    sum(ol_amount) as sum_amount,
    avg(ol_quantity) as avg_qty,
    avg(ol_amount) as avg_amount,
    count(*) as count_order
from 
    order_line, stock, supplier, nation
where
    ol_supply_w_id = s_w_id
    and ol_i_id = s_i_id
    and s_suppkey = su_suppkey
    and su_nationkey = n_nationkey
    and n_name = 'Canada'
    and ol_delivery_d > '2015-01-02 00:00:00.000000'
group by 
    ol_number 
order by 
    ol_number;
"""
,
"""
-- Q02
select 
    su_suppkey, su_name, n_name, i_id, i_name, su_address, su_phone, su_comment
from 
    item, supplier, stock, nation,
    (
     select 
         s_i_id as m_i_id,
         min(s_quantity) as m_s_quantity
     from 
         stock, 
         supplier, 
         nation
     where 
         s_suppkey = su_suppkey
         and su_nationkey = n_nationkey
         and n_name like 'Canada%'   
     group by 
         s_i_id
    ) m
where 
    i_id = s_i_id
    and s_suppkey = su_suppkey
    and su_nationkey = n_nationkey
    and i_brand like 'Brand#31%'    
    and n_name like 'Canada%'
    and i_id = m_i_id
    and s_quantity = m_s_quantity
order by 
    n_name, su_name, i_id;
"""
,
"""
/*+ SeqScan(order_line) */
-- Q03
select 
    ol_o_id, ol_w_id, ol_d_id, sum(ol_amount) as revenue, o_entry_d
from 
    customer, new_order, orders, order_line, nation
where 
    c_state like 'S%'
    and c_id = o_c_id
    and c_w_id = o_w_id
    and c_d_id = o_d_id
    and no_w_id = o_w_id
    and no_d_id = o_d_id
    and no_o_id = o_id
    and ol_w_id = o_w_id
    and ol_d_id = o_d_id
    and ol_o_id = o_id
    and c_nationkey = n_nationkey
    and n_name like 'Canada%'
group by 
    ol_o_id, ol_w_id, ol_d_id, o_entry_d
order by 
    revenue desc, o_entry_d;
"""
,
"""
/*+ SeqScan(order_line) */
-- Q04
select 
    o_ol_cnt, count(*) as order_count
from 
    orders, customer, nation
where 
    o_entry_d >= '2015-01-02 00:00:00.000000'
    and o_entry_d < '2025-01-02 00:00:00.000000'
    and c_id = o_c_id
    and c_w_id = o_w_id
    and c_d_id = o_d_id
    and c_nationkey = n_nationkey
    and n_name like 'Canada%'
    and exists (
        select 
            *
        from 
            order_line
        where o_id = ol_o_id
            and o_w_id = ol_w_id
            and o_d_id = ol_d_id
            and ol_delivery_d >= o_entry_d)
group by 
    o_ol_cnt
order by 
    o_ol_cnt;
"""
,
"""
-- Q05
select
    cust_nation.n_name, sum(ol_amount) as revenue
from 
    customer, orders, order_line, stock, supplier, nation cust_nation, nation supp_nation
where 
    c_id = o_c_id
    and c_w_id = o_w_id
    and c_d_id = o_d_id
    and ol_o_id = o_id
    and ol_w_id = o_w_id
    and ol_d_id = o_d_id
    and ol_w_id = s_w_id
    and ol_i_id = s_i_id
    and s_suppkey = su_suppkey
    and c_nationkey = cust_nation.n_nationkey
    and su_nationkey = supp_nation.n_nationkey
    and cust_nation.n_name like 'Canada%'
    and supp_nation.n_name like 'Canada%' 
    and o_entry_d >= '2015-01-02 00:00:00.000000'
group by 
    cust_nation.n_name
order by 
    revenue desc;
"""
,
"""
-- Q06
select 
   sum(ol_amount) as revenue
from 
   order_line, stock, supplier, nation
where
   ol_supply_w_id = s_w_id
   and ol_i_id = s_i_id
   and s_suppkey = su_suppkey
   and su_nationkey = n_nationkey
   and n_name like 'Canada%'
   and ol_delivery_d >= '2015-01-02 00:00:00.000000'
   and ol_delivery_d < '2025-01-02 00:00:00.000000'
   and ol_quantity between 1 and 100000;
"""
,
"""
-- Q07
select 
   n1.n_name as supp_nation,
   n2.n_name as cust_nation,
   extract(year from o_entry_d) as l_year,
   sum(ol_amount) as revenue
from 
   supplier, stock, order_line, orders, customer, nation n1, nation n2
where 
   ol_supply_w_id = s_w_id
   and ol_i_id = s_i_id
   and s_suppkey = su_suppkey
   and ol_w_id = o_w_id
   and ol_d_id = o_d_id
   and ol_o_id = o_id
   and c_id = o_c_id
   and c_w_id = o_w_id
   and c_d_id = o_d_id
   and su_nationkey = n1.n_nationkey
   and c_nationkey = n2.n_nationkey
   and (
    (n1.n_name = 'Germany' and n2.n_name = 'Cambodia')
    or
    (n1.n_name = 'Cambodia' and n2.n_name = 'Germany')
   )   and ol_delivery_d between '2015-01-02 00:00:00.000000' and '2025-01-02 00:00:00.000000'
group by 
   supp_nation, cust_nation, l_year
order by 
   supp_nation, cust_nation, l_year;
"""
,
"""
-- Q08
select 
    extract(year from o_entry_d) as l_year,
    sum(case when n2.n_name = 'Germany' then ol_amount else 0 end) / sum(ol_amount) as mkt_share
from 
    item, supplier, stock, order_line, orders, customer, nation n1, nation n2
where 
    i_id = s_i_id
    and ol_i_id = s_i_id
    and ol_supply_w_id = s_w_id
    and s_suppkey = su_suppkey
    and ol_w_id = o_w_id
    and ol_d_id = o_d_id
    and ol_o_id = o_id
    and c_id = o_c_id
    and c_w_id = o_w_id
    and c_d_id = o_d_id
    and n1.n_nationkey = c_nationkey
    and ol_i_id < 1000
    and n1.n_name like 'Canada%'
    and su_nationkey = n2.n_nationkey
    and i_brand like 'Brand#21%'
    and s_i_id = ol_i_id
group by 
    extract(year from o_entry_d)
order by 
    l_year;
"""
,
"""
-- Q09
select 
    n_name, extract(year from o_entry_d) as l_year, sum(ol_amount) as sum_profit
from 
    item, stock, supplier, order_line, orders, nation
where 
    ol_i_id = s_i_id
    and ol_supply_w_id = s_w_id
    and s_suppkey = su_suppkey
    and ol_w_id = o_w_id
    and ol_d_id = o_d_id
    and ol_o_id = o_id
    and ol_i_id = i_id
    and su_nationkey = n_nationkey
    and i_brand like 'Brand#21%'
    and n_name like 'Botswana%'
group by 
    n_name, extract(year from o_entry_d)
order by 
    n_name, l_year desc;
"""
,
"""
-- Q10
select 
    c_id, c_last, sum(ol_amount) as revenue, c_city, c_phone, n_name
from 
    customer, orders, order_line, nation
where 
    c_id = o_c_id
    and c_w_id = o_w_id
    and c_d_id = o_d_id 
    and ol_w_id = o_w_id
    and ol_d_id = o_d_id 
    and ol_o_id = o_id
    and o_entry_d <= ol_delivery_d
    and n_nationkey = c_nationkey
    and n_name like 'Canada%'
group by 
    c_id, c_last, c_city, c_phone, n_name
order by 
    revenue desc;
"""
,
"""
-- Q11
select 
    s_i_id, sum(s_order_cnt) as ordercount
from 
    stock, supplier, nation
where 
    s_suppkey = su_suppkey
    and su_nationkey = n_nationkey
    and n_name = 'Germany'
group by 
    s_i_id
having 
    sum(s_order_cnt) >
        (select 
             sum(s_order_cnt) * .005
         from 
             stock, supplier, nation
         where s_suppkey = su_suppkey
             and su_nationkey = n_nationkey
             and n_name = 'Germany')
order by 
    ordercount desc;
"""
,
"""
-- Q12
select 
    o_ol_cnt,
    sum(case when o_carrier_id = 1 or o_carrier_id = 2 then 1 else 0 end) as high_line_count,
    sum(case when o_carrier_id <> 1 and o_carrier_id <> 2 then 1 else 0 end) as low_line_count
from 
    orders, order_line, customer, nation
where     c_id = o_c_id
    and c_w_id = o_w_id
    and c_d_id = o_d_id 
    and c_nationkey = n_nationkey
    and n_name like 'Canada%'
    and ol_w_id = o_w_id
    and ol_d_id = o_d_id
    and ol_o_id = o_id
    and o_entry_d <= ol_delivery_d
group by 
    o_ol_cnt
order by 
    o_ol_cnt;
"""
,
"""
-- Q14
select 
    100.00 * sum(case when i_data like 'PR%' then ol_amount else 0 end) / (1+sum(ol_amount)) as promo_revenue
from 
    order_line, item
where 
    ol_i_id = i_id
    and i_brand = 'Brand#41';
"""
,
"""
-- Q15
with revenue (supplier_no, total_revenue) as 
(select 
    s_suppkey as supplier_no,
    sum(ol_amount) as total_revenue
from 
    order_line, stock, item
where 
    ol_i_id = s_i_id 
    and ol_supply_w_id = s_w_id
    and s_i_id = i_id
    and i_brand like 'Brand#34%'
group by 
    supplier_no)
select 
    su_suppkey, su_name, su_address, su_phone, total_revenue
from 
    supplier, revenue
where 
    su_suppkey = supplier_no
    and total_revenue = (
        select 
            max(total_revenue) 
        from 
            revenue)
order by 
    su_suppkey;
"""
,
"""
-- Q16
select 
    i_name, i_brand as brand, i_price, count(distinct s_suppkey) as supplier_cnt
from 
    stock, item
where 
    i_id = s_i_id
    and i_brand like 'Brand#31%'
    and (s_suppkey not in
         (select su_suppkey
          from supplier
          where su_comment like '%bad%'))
group by 
    i_name, i_brand, i_price
order by 
    supplier_cnt desc;
"""
,
"""
-- Q18
select 
    c_last, c_id, o_id, o_entry_d, o_ol_cnt, sum(ol_amount)
from 
    customer, orders, order_line, nation
where 
    c_id = o_c_id
    and c_w_id = o_w_id
    and c_d_id = o_d_id
    and ol_w_id = o_w_id
    and ol_d_id = o_d_id
    and ol_o_id = o_id
    and c_nationkey = n_nationkey
    and n_name like 'Canada%' 
group by 
    o_id, o_w_id, o_d_id, c_id, c_last, o_entry_d, o_ol_cnt
having 
    sum(ol_amount) > 200
order by 
    sum(ol_amount) desc, o_entry_d;
"""
]

sent_query_amount = 0
is_terminated = False
file_suffix="0"
lock = Lock()

RANDOM_SEED = 123
query_nums=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 18]
#query_nums=[1, 2, 3, 6, 7, 8]

def start_ch_thread(start_index,pgpath):
	global sent_query_amount
	global ch_queries
	global is_terminated

	size = len(ch_queries)

	cur_index = start_index
	while not is_terminated:
		return_code = send_query(ch_queries[cur_index], cur_index, pgpath)
		# if there was an error, we will retry the same query
		if return_code != 0:
			continue

		sent_query_amount += 1

		# Send same query
		cur_index += 1
		cur_index %= size

def send_query(query,cur_index,pgpath):
	global coord_ip, query_nums
	pg = ['%s/pgsql/bin/psql'%(pgpath), '-P', 'pager=off', '-v', 'ON_ERROR_STOP=1', '-h', coord_ip, '-c', query]

	start_time = int(round(time.time() * 1000))
	return_code = subprocess.call(pg)
	end_time = int(round(time.time() * 1000))

	with open("./results/ch_queries_{}.txt".format(file_suffix), "a") as f:
		res = "{} finished in {} milliseconds".format(query_nums[cur_index], end_time - start_time)
		f.write(res+"\n")
		print(res, file=sys.stderr)

	return return_code

def give_stats(sent_query_amount, time_lapsed_in_secs):
	with open("./results/ch_results_{}.txt".format(file_suffix), "w") as f:
		f.write("queries {} in {} seconds\n".format(sent_query_amount, time_lapsed_in_secs))
		f.write("QPH {}\n".format(3600.0 * sent_query_amount / time_lapsed_in_secs))

def get_curtime_in_seconds():
	return int(round(time.time()))


def terminate():
	global is_terminated
	global sent_query_amount
	global start_time_in_secs

	end_time_in_secs = get_curtime_in_seconds()

	give_stats(sent_query_amount, end_time_in_secs - start_time_in_secs)

	is_terminated = True

class GracefulKiller:
	kill_now = False
	def __init__(self):
		signal.signal(signal.SIGINT, self.exit_gracefully)
		signal.signal(signal.SIGTERM, self.exit_gracefully)

	def exit_gracefully(self,signum, frame):
		global is_terminated
		self.kill_now = True
		print("got a kill signal")
		terminate()

if __name__ == "__main__":

	thread_count = int(sys.argv[1])
	coord_ip = sys.argv[2]
	initial_sleep_in_mins=int(sys.argv[3])
	file_suffix=sys.argv[4]
	pgpath = sys.argv[5]

	random.seed(RANDOM_SEED)

	# start_indexes = list(range(0, len(ch_queries)))
	# random.shuffle(start_indexes)
 
	interval = len(ch_queries) // thread_count

	jobs = [
		Thread(target = start_ch_thread, args=((i*interval) % len(ch_queries), pgpath))
		for i in range(0, thread_count)]

	sleep(initial_sleep_in_mins * 60)

	start_time_in_secs = get_curtime_in_seconds()
	for j in jobs:
		j.start()

	killer = GracefulKiller()
	while not killer.kill_now:
		time.sleep(10)
