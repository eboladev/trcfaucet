import sqlite3
from SendCoin import Coupon

# Load Database
DATABASE_FILE = '/root/trc.db'


# Welcome Message and Choice
print("Welcome to Coupon Manager...")
print("1) Generate Coupons")
print("2) Clear Expired Coupons")
choice = input("option: ")

# Generate Coupons
if choice == 1:
	# Input Params
	coupon_num = input("Number of Coupons: ")
	coupon_val = input("Coupon Value: ")
	coupon_use = input("Number of Uses: ")

	# Warning String
	chk_str = "Are you sure you want to create coupon(s) with the following "
	chk_str += "parameters(y/n):\n (Coupons: {0} / Value: {1} / Uses: {2}) \n"
	chk_str = chk_str.format(coupon_num, coupon_val, coupon_val)

	# Create Coupons
	if input(check) == "y":
		# Connect to Database
		conn = sqlite3.connect(DATABASE_FILE)
		mc = Coupon(conn)
		coupon_list = []

		# Create Coupons
		for i in range(coupon_num):
			coupon_list.append(mc.new("CAP_USE", coupon_val, coupon_use))

		# Output Coupon Codes:
		print("Coupon Codes:\n")
		for i in coupon_list: print(i)
		print("Done...")

# Clear Expired Coupons
elif choice == 2:
	if input("Are you sure(y/n)?") == 'y':
		conn = sqlite3.connect(DATABASE_FILE)
		Coupon(conn).clear()
		print("Done...")

# Close Database
print("Exiting...")
conn.close()	