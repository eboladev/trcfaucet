import sqlite3
from SendCoin import Coupon

# Load Database
DATABASE_FILE = '/root/trc.db'
conn = sqlite3.connect(DATABASE_FILE)

# Create Coupon
mc = Coupon(conn)
coupon_val = sys.argv[1]
coupon_use = sys.argv[2]
out = mc.new("CAP_USE", coupon_val, coupon_use)