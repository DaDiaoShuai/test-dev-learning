# -- 用 sqlite3，建一张 orders(id, user, amount, status) 表并插入 8 行数据，完成这 3 个查询：

# -- 查 status='paid' 的订单数
# -- 按 user 分组统计总金额
# -- 找出金额 >100 的前 3 单

import sqlite3

conn = sqlite3.connect("my.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# cur.excute("INSERT INTO orders (id, user, amout, status) VALUES (?, ?, ?, ?), ()")

# -- 查 status='paid' 的订单数
SELECT COUNT(*) AS paid_count
FROM orders
WHERE status = 'paid';

# 按 user 分组统计总金额
SELECT user, SUM(amount) AS total_amount
FROM orders
GROUP BY user
ORDER BY total_amount DESC;

# 找出金额 >100 的前 3 单
SELECT * FROM orders
WHERE amount > 100
ORDER BY amount DESC
LIMIT 3;