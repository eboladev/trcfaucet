import sqlite3
import commands
from time import sleep
from CryptoTap import DripRequest


# Globals ----------------------------------------------------------------------
DATABASE_FILE = '/root/trc.db'
DATABASE_TABLE = 'drip_request'
COIN_CLIENT = 'terracoind'
COIN_NAME = 'TRC'
DEFAULT_SEND_VAL = 0.0001
HARD_LIMIT = 0.01
LOW_BAL_LIMIT = 0.001


# Coupon System  ---------------------------------------------------------------
class Coupon:
	def __init__(self,conn):
		"""
		Validates coupons. Also allows the admin to create new coupons of the 
		following types:

		SINGLE_USE - Only redeems once for a set value.
		CAP_USE - Only a set number of coupons can be redeemed.

		"""
		self.conn = conn
		self.cursor = conn.cursor()

	def new(self, coup_type, coup_value, max_use = 1):
		query = "INSERT INTO coupon_list (id, coup_type, coup_value, max_use, access_key)"
		query += "VALUES (NULL, ?, ?, ?, ?)"

		if coupon_type == 'SINGLE_USE' or coupon_type == 'CAP_USE':
			pass
		else:
			return "Unrecognized coupon type."

		access_key = gen_access_key()

		self.cursor.execute(query, (coup_type, coup_value, max_use, access_key,))
		self.conn.commit()

		return access_key

	def gen_access_key(self):
		return str(hashlib.sha1(str(random.random())).hexdigest())[:10]

	def search(self, access_key):
		query = "select * from coupon_list where access_key=? limit 1"
		self.cursor.execute(query, (access_key,))
		return self.cursor.fetchone()

	def use(self, access_key):
		coupon = self.search(access_key)
		print(coupon)
		if coupon == None: return 0

		coup_id = coupon[0]
		coup_val = coupon[2]
		max_use = coupon[3]

		if max_use >= 1:
			query = "update coupon_list set max_use=(max_use - 1) where id=?"
			self.cursor.execute(query, (coup_id,))
			self.conn.commit()
			return coup_val

		return 0
		
	def lookup(self, coupon):
		"""Returns the spend value for a particular coupon."""
		if coupon == "MOREMONEY": return 0.00015
		elif coupon == "DOUBLEMONEY": return 0.0002
		return 0.0001


# Send Functions ---------------------------------------------------------------
def get_balance():
	"Retrieves the current balance."
	com = '{0} getbalance'
	return float(commands.getstatusoutput(com.format(COIN_CLIENT))[1])

def com_send(drip_id, address, coupon, amount, conn):
		"""
		Send the specified amount to the drip request, time whatever the
		coupon code specifies. Uses the following unix command to do so:
			sendtoaddress <terracoinaddress> <amount> [comment] [comment-to]
		The comment arguments are optional, and not currently used. 

		"""

		# Check coupon amount
		coupon_val = float(Coupon(conn).use(coupon))
		if coupon_val > 0:
			amount = coupon_val
		else:
			amount = DEFAULT_SEND_VAL

		# Hardcoded limit at 0.1 TRC in case the coupon system breaks
		if amount > HARD_LIMIT: amount = HARD_LIMIT
		
		# Make sure balance is not empty before sending
		if (get_balance() - amount) > LOW_BAL_LIMIT:
			# Construct Command
			command = "{0} sendtoaddress {1} {2}"
			command = command.format(COIN_CLIENT, str(address), str(amount))
			trans_id = commands.getstatusoutput(command)[1]

			# Update
			c = conn.cursor()
			query = "update drip_request set trans_id=? where id=?"
			c.execute(query, (trans_id, drip_id,))
			conn.commit()

			# Console Message
			con_message = "Sent {0} {1} to {2}. Traction ID: {3}"
			return con_message.format(amount, COIN_NAME, address, trans_id)
		else:
			return "Insufficient Funds!"


def send_coins():
	"""Sends queued coins."""
	# Connect to Database
	conn = sqlite3.connect(DATABASE_FILE)
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
						 DEFAULT_SEND_VAL, conn)
		except ValueError as detail: 
			return "Something Broke: " + str(detail) 
		#except:	return "Something Broke..."

	# Close Database
	conn.close()


# Infinite Loop ----------------------------------------------------------------
while True:
	print("Checking for drips...")
	print(send_coins())
	print("Sleeping for 15 seconds...")
	sleep(15)