import sqlite3
from flask import Flask
from Coupon import Coupon

# Load Database
app = Flask(__name__)
app.config.from_pyfile('settings.cfg')

# Welcome Message and Choice
print("Welcome to Coupon Manager...")
print("1) Generate Coupons")
print("2) Clear Expired Coupons")
choice = input("option: ")

# Generate Coupons
if int(choice) == 1:
	# Input Params
	coupon_num = int(input("Number of Coupons: "))
	coupon_val = float(input("Coupon Value: "))
	coupon_use = int(input("Number of Uses: "))

	# Warning String
	chk_str = "Are you sure you want to create coupon(s) with the following "
	chk_str += "parameters(y/n):\n (Coupons: {0} / Value: {1} / Uses: {2}) \n"
	chk_str = chk_str.format(coupon_num, coupon_val, coupon_use)

	# Create Coupons
	if str(input(chk_str)) == 'y':
		# Connect to Database
		conn = sqlite3.connect(app.config['DATABASE_FILE'])
		mc = Coupon(conn)
		coupon_list = []

		# Create Coupons
		for i in range(coupon_num):
			new_coup = mc.new(coupon_val, coupon_use)
			coupon_list.append(new_coup)

		# Output Coupon Codes:
		print("Coupon Codes:\n")
		for i in coupon_list: print(i)
		print("Done...")
		conn.close()	

# Clear Expired Coupons
elif int(choice) == 2:
	if str(input("Are you sure(y/n)?")) == 'y':
		conn = sqlite3.connect(app.config['DATABASE_FILE'])
		Coupon(conn).clear()
		print("Done...")
		conn.close()	

# Close Database
print("Exiting...")