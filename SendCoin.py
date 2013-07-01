import random
import sqlite3
import hashlib
import commands
from time import sleep
from flask import Flask
from CryptoTap import DripRequest


# Load Settings  ---------------------------------------------------------------
app = Flask(__name__)
app.config.from_pyfile('settings.cfg')


# Coupon System  ---------------------------------------------------------------
class Coupon:
	def __init__(self, conn):
		"""
		Object that allows the admin to create and manage coupons. Also allows
		the system to validate and lookup coupons. 

		"""
		self.conn = conn
		self.cursor = self.conn.cursor()

	def new(self, coup_value, max_use = 1):
		query = "INSERT INTO coupon_list (id, coup_value, max_use, access_key)"
		query += "VALUES (NULL, ?, ?, ?)"

		access_key = str(self.gen_access_key()).lower()

		self.cursor.execute(query, (coup_value, max_use, access_key,))
		self.conn.commit()

		return access_key

	def gen_access_key(self):
		return str(hashlib.sha1(str(random.random())).hexdigest())[:10]

	def search(self, access_key):
		print(access_key)
		query = "select * from coupon_list where access_key=? limit 1"
		self.cursor.execute(query, (access_key.lower(),))
		return self.cursor.fetchone()

	def use(self, access_key):
		coupon = self.search(access_key)
		if coupon == None: return 0

		coup_id = coupon[0]
		coup_val = coupon[1]
		max_use = coupon[2]

		if max_use >= 1:
			query = "update coupon_list set max_use=(max_use - 1) where id=?"
			self.cursor.execute(query, (coup_id,))
			self.conn.commit()
			return coup_val

		return 0

	def clear(self):
		query = "delete from coupon_list where max_use=0"
		self.cursor.execute(query)
		self.conn.commit()
		

# Send Functions ---------------------------------------------------------------
def get_balance():
	"Retrieves the current balance."
	com = '{0} getbalance'
	return float(commands.getstatusoutput(com.format(app.config['COIN_CLIENT']))[1])

def com_send(drip_id, address, coupon, amount, conn):
		"""
		Send the specified amount to the drip request, time whatever the
		coupon code specifies. Uses the following unix command to do so:
			sendtoaddress <terracoinaddress> <amount> [comment] [comment-to]
		The comment arguments are optional, and not currently used. 

		"""

		# Check coupon amount
		coupon_val = float(Coupon(conn).use(coupon))
		print(coupon_val)
		if coupon_val > 0: amount = coupon_val
		else: amount = float(app.config['DEFAULT_SEND_VAL'])
		print(amount)

		# Hardcoded limit at 0.1 TRC in case the coupon system breaks
		if amount > app.config['HARD_LIMIT']: amount = app.config['HARD_LIMIT']
		
		# Make sure balance is not empty before sending
		if (get_balance() - amount) > app.config['LOW_BAL_LIMIT']:
			# Construct Command
			command = "{0} sendtoaddress {1} {2}"
			command = command.format(str(app.config['COIN_CLIENT']), str(address), str(amount))
			trans_id = commands.getstatusoutput(command)[1]
			print(command)

			# Update
			c = conn.cursor()
			query = "update drip_request set trans_id=? where id=?"
			c.execute(query, (trans_id, drip_id,))
			conn.commit()

			# Console Message
			con_message = "Sent {0} {1} to {2}. Traction ID: {3}"
			return con_message.format(amount, app.config['COIN_NAME'], address, trans_id)
		else:
			return "Insufficient Funds!"


def send_coins():
	"""Sends queued coins."""
	# Connect to Database
	conn = sqlite3.connect(app.config['DATABASE_FILE'])
	c = conn.cursor()

	# Do Query
	query = "select * from drip_request where trans_id=? limit 1"
	c.execute(query, ("UNSENT",))

	row = c.fetchone()
	if row == None:
		return "No drips found..."
	else:
		try:
			drip = DripRequest(row[3], row[4], row[2], row[0])
			return com_send( drip.drip_id, drip.address, drip.coupon,
						 app.config['DEFAULT_SEND_VAL'], conn)
		except ValueError as detail: 
			return "Something Broke: " + str(detail) 
		#except:	return "Script Fail..."

	# Close Database
	conn.close()


# Infinite Loop ----------------------------------------------------------------
if __name__ == '__main__':
	check_timeout = int(app.config['CHECK_SEND_SEC'])
	while True:
		print("Checking for drips...")
		print(send_coins())
		print("Sleeping for {0} seconds...".format(check_timeout))
		sleep(check_timeout)