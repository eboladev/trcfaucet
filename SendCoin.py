import sqlite3
import commands
from time import sleep
from CryptoTap import Coupon
from CryptoTap import DripRequest


# Globals ----------------------------------------------------------------------
DATABASE_FILE = '/root/trc.db'
COIN_CLIENT = 'terracoind'
DEFAULT_SEND_VAL = 0.0001
HARD_LIMIT = 0.01
LOW_BAL_LIMIT = 0.001


# Send Function ----------------------------------------------------------------
def get_balance(self):
	"Retrieves the current balance."
	return float(commands.getstatusoutput('{0} getbalance'.format(COIN_CLIENT))[1])

def send(self, drip_id, address, coupon, amount, conn):
		"""
		Send the specified amount to the drip request, time whatever the
		coupon code specifies. Uses the following unix command to do so:
			sendtoaddress <terracoinaddress> <amount> [comment] [comment-to]
		The comment arguments are optional, and not currently used. 

		"""

		# Make Shell Command
		amount *= Coupon.lookup(coupon)
		 # hardcoded limit at 0.1 TRC in case the coupon system breaks
		if amount > HARD_LIMIT: amount = HARD_LIMIT
		
		if (get_balance() - amount) > LOW_BAL_LIMIT:
			# Construct Command
			command = '{0} sendtoaddress {1} {2}'
			command = command.format(COIN_CLIENT, self.address, str(amount))
			trans_id = commands.getstatusoutput(command)[1]

			# Update
			c = conn.cursor()
			query = "update drip_request set trans_id = '{0}' where id = {1}"
			query = query.format(trans_id, drip_id)
			c.execute(query)
			conn.commit()

			# Console Message
			con_message = "Sent {0} {1} to {2}. Traction ID: {3}"
			return con_message.format(amount, COIN_NAME, self.address, trans_id)
		else:
			return "Insufficient Funds!"


def send_coins():
	"""Sends queued coins."""
	# Connect to Database
	conn = sqlite3.connect(DATABASE_FILE)
	c = conn.cursor()

	# Do Query
	query = "SELECT * FROM drip_request WHERE trans_id='UNSENT' LIMIT 1"
	c.execute(query.format("UNSENT"))

	row = c.fetchone()
	if row == None:
		return "No drips found..."
	else:
		try:
			drip = DripRequest(row[3], row[4], row[2], row[0])
			return send( drip.drip_id, drip.address, drip.coupon, DEFAULT_SEND_VAL, conn)

		except ValueError: return "Something Broke(ValueError)..." 
		except:	return "Something Broke(SomeError)..."

	# Close Database
	conn.close()


# Infinite Loop ----------------------------------------------------------------
while True:
	print("Checking for drips...")
	print(send_coins())
	print("Sleeping for 5 seconds...")
	sleep(5)