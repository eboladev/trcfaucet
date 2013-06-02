import sqlite3
from SendCoin import Coupon

DATABASE_FILE = '/root/trc.db'
conn = sqlite3.connect(DATABASE_FILE)

mc = Coupon(conn)
out = mc.new("CAP_USE", 0.0002, 10)
print(out)