import sqlite3
import commands
from time import sleep
from CryptoTap import Coupon
from CryptoTap import DripRequest


# Globals ----------------------------------------------------------------------
DATABASE_FILE = '/root/trc.db'
DATABASE_TABLE = 'drip_request'
COIN_CLIENT = 'terracoind'
COIN_NAME = 'TRC'
DEFAULT_SEND_VAL = 0.0001
HARD_LIMIT = 0.01
LOW_BAL_LIMIT = 0.001


# Send Function ----------------------------------------------------------------
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
		amount *= Coupon().lookup(coupon)

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
			query = "update drip_request set trans_id = ? where id = ?"
			c.execute(query, (trans_id, drip_id))
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
	query = "SELECT * FROM ? WHERE trans_id=? LIMIT 1"
	c.execute(query, (DATABASE_TABLE, "UNSENT"))

	row = c.fetchone()
	if row == None:
		return "No drips found..."
	else:
		try:
			drip = DripRequest(row[3], row[4], row[2], row[0])
			return com_send( drip.drip_id, drip.address, drip.coupon,
						 DEFAULT_SEND_VAL, conn)
		except ValueError as detail: 
			return "Something Broke: " + detail 
		except:	return "Something Broke..."

	# Close Database
	conn.close()


# Infinite Loop ----------------------------------------------------------------
while True:
	print("Checking for drips...")
	print(send_coins())
	print("Sleeping for 15 seconds...")
	sleep(15)