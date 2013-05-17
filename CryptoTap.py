import os
import re
import string
import sqlite3
import hashlib
import commands
from random import randrange
from datetime import datetime
from datetime import timedelta

from flask import g
from flask import abort
from flask import Flask
from flask import url_for
from flask import request
from flask import redirect
from flask import render_template
from contextlib import closing


# Global Configs
DATABASE = '/root/trc.db'
DEBUG = True
SECRET_KEY = '31491de80d74f54da681c40cc4d08c41a35939ac'
USERNAME = 'trcadmin'
PASSWORD = 'trcs3cur3'

DATABASE_TABLE = 'drip_request'
DEFAULT_SEND_VAL = 0.0001
COIN_NAME = "TRC"
COIN_CLIENT = "terracoind"
REQUEST_LIMIT = 3


# Load Flask
app = Flask(__name__)
app.config.from_object(__name__)

# Database Functions
def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception): 
	if hasattr(g, 'db'):
		g.db.close()

def init_db():
	with closing(connect_db()) as db:
		with app.open_resource('schema.sql') as f:
			db.cursor().executescript(f.read())
		db.commit()

def get_connection():
    db = getattr(g, '_db', None)
    if db is None:
        db = g._db = connect_db()
    return db

def query_db(query, args=(), one=False):
	cur = g.db.execute(query, args)
	rv = [dict((cur.description[idx][0], value)
		for idx, value in enumerate(row)) for row in cur.fetchall()]
	return (rv[0] if rv else None) if one else rv


# Helper Functions
def sub_cypher(ip, offset):
	"""Number substitution offset cypher(protect ips). Don't use offset values 0-9."""
	# Implement Better Cypher: rotate((ip % sum1bits(ip) ), sum0bits(ip))
	return [(abs(int(x) - offset)%10) if x.isdigit() else '.' for x in ip]

def get_html(save_time, ip, trans_id):
	"""Transform database output into a table."""
	diff_time = datetime.now() - datetime.strptime(save_time, "%Y-%m-%d %H:%M:%S")
	diff_time = divmod(diff_time.seconds, 60)
	diff_time = "{0} mins, {1} secs ago".format(diff_time[0], diff_time[1])
	obfuscated_ip = ''.join(map(str, sub_cypher(list(ip), 655)))
	if trans_id == "UNSENT":
		html = "<tr><td>{0}</td><td>{1}</td><td>Processing...</td></tr>"
		html = html.format(diff_time, obfuscated_ip)
	else:
		short_trans_id = trans_id[:37] + "..."
		trans_id_url = "http://cryptocoinexplorer.com:3750/tx/{0}".format(trans_id)
		html = "<tr><td>{0}</td><td>{1}</td><td><a href='{2}'>{3}</a></td></tr>"
		html = html.format(diff_time, obfuscated_ip, trans_id_url, short_trans_id)
	
	return html

def send_coins():
	"""Sends queued coins."""
	recent_drips = g.db.execute('SELECT * FROM drip_request ORDER BY id DESC LIMIT 5')
	recent_drips = recent_drips.fetchall()

	if len(recent_drips) >= 0: print("No Drips Found.")
	else: print("Found {0} Drips".format(len(unsent)))

	for row in recent_drips:
		drip = DripRequest(row[3], row[4], row[2], row[0])
		print(drip.send(DEFAULT_SEND_VAL))

def get_index(form_submit_status = None):
	"""Displays the default index page, or a success/error page."""
	captcha = (randrange(1, 15), randrange(1, 15))
	captcha_awns = hashlib.sha1(str(captcha[0] + captcha[1])).hexdigest()

	recent_drips = g.db.execute('SELECT * FROM drip_request ORDER BY id DESC LIMIT 10')
	recent_drips_html = [get_html(row[1], row[2], row[5]) for row in recent_drips.fetchall()]
	recent = ''.join(map(str, recent_drips_html))
	
	cur = g.db.execute('SELECT Count(*) FROM drip_request')
	stats = 3060 + int(cur.fetchone()[0])

	return render_template('index.html', recent=recent, form_submit=form_submit_status,
						   captcha=captcha, captcha_awns=captcha_awns, stats=stats)


# Hard Coded Coupons
def lookup_coupon(coupon):
	if coupon == "MOREMONEY": return 1.5
	elif coupon == "DOUBLEMONEY": return 2
	return 1 


class DripValidate:
	def __init__(self):
		"""Used to validate input before database use."""
		pass

	def clean(self, in_str):
		"""Strips out string that is not alphanumeric. Should stop injects."""
		pattern = re.compile('[\W_]+')
		return pattern.sub('', in_str)

	def validate_address(self, address):
		# Source: http://bit.ly/17OhFP5
		"""
		Does simple validation of a bitcoin address. 

		param : address : an ASCII or unicode string, of a bitcoin address.
		returns : boolean, indicating that the address has a correct format.

		"""
		
		address = self.clean(address)
		# The first character indicates the "version" of the address.
		CHARS_OK_FIRST = "123"
		# alphanumeric characters without : l I O 0
		CHARS_OK = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
		
		# We do not check the high length limit of the adress. 
		# Usually, it is 35, but nobody knows what could happen in the future.
		if len(address) < 27:
			return False
		elif address[0] not in CHARS_OK_FIRST:
			return False

		# We use the function "all" by passing it an enumerator as parameter. 
		# It does a little optimisation : 
		# if one of the character is not valid, the next ones are not tested.
		return all( ( char in CHARS_OK for char in address[1:] ) )
	
	def validate_coupon(self, coupon):
		"""Makes sure the coupon is alphanumeric and less than 12 chars."""
		coupon = self.clean(coupon)
		cond1 = re.match('^[\w]+$', coupon) and len(coupon)<12
		cond2 = (lookup_coupon(coupon) != 1)
		return (cond1 and cond2)

	def validate_ip(self, ip):
		"""Checks if it is a valid IP address."""
		return re.match('([0-9]{1,3}\.){3}[0-9]+',ip)	


class DripRequest:
	"""
	Stores a users terracoin send request. 

	Data Members:
	address -- Terracoin address to send the transaction to.
	coupon  -- Special code that allows users to get additional coins.
	ip      -- The IP address that the request was made from.
	drip_id -- The database id of the drip request.
	
	"""
	def __init__(self, address, coupon, ip, drip_id = 0):
		vall = DripValidate()
		if not vall.validate_address(str(address)): 
			raise ValueError("Invalid Terracoin Address.")
		elif not vall.validate_coupon(str(coupon)): coupon = "INVALID"
		elif not vall.validate_ip(str(ip)): raise ValueError("Invalid IP.")

		self.address = str(address)
		self.coupon = str(coupon).upper()
		self.ip = str(ip)
		self.drip_id = drip_id

	def __str__(self):
		text = '{0} {1} {2} {3} {4}'
		return text.format(self.address, self.coupon, self.ip, self.drip_id)

	def count_unique(self, row, val):
		query = "SELECT Count(*) FROM drip_request WHERE {0} = '{1}'"
		cur = g.db.execute(query.format(row, val))
		return int(cur.fetchone()[0])

	def save(self):
		"""Insert drip request into database."""
		num_ip = self.count_unique("ip", self.ip)
		num_address = self.count_unique("address", self.address)
		request_str = "IP: {0}/{1} and Address: {2}/{3}"
		print(request_str.format(num_ip, REQUEST_LIMIT, num_address, REQUEST_LIMIT))
		if num_ip < REQUEST_LIMIT and num_address < REQUEST_LIMIT:
			query = "INSERT INTO drip_request (id, crdate, ip, address, coupon, trans_id)"
			query += "VALUES (NULL, datetime('now'),'{0}','{1}','{2}','{3}')"
			g.db.execute(query.format(self.ip, self.address, self.coupon, "UNSENT"))
			g.db.commit()

		else:
			raise LookupError

	def get_balance(self):
		"Retrieves the current balance."
		return float(commands.getstatusoutput('{0} getbalance'.format(COIN_CLIENT))[1])

	def send(self, amount):
		"""
		Send the specified amount to the drip request, time whatever the
		coupon code specifies. Uses the following unix command to do so:
			sendtoaddress <terracoinaddress> <amount> [comment] [comment-to]
		The comment arguments are optional, and not currently used. 

		"""
		# Make Shell Command
		amount *= lookup_coupon(self.coupon)
		 # hardcoded limit at 0.1 TRC in case the coupon system breaks
		if amount > 0.1: amount = 0.1
		
		if (self.get_balance() - amount) > 0.001:
			# Construct Command
			command = '{0} sendtoaddress {1} {2}'
			command = command.format(COIN_CLIENT, self.address, str(amount))
			trans_id = commands.getstatusoutput(command)[1]
		 
			# Send Payment
			query = 'update drip_request set trans_id = '{0}' where id = {1}'
			g.db.execute(query.format(trans_id, self.drip_id))
			g.db.commit()

			# Console Message
			con_message = "Sent {0} {1} to {2}. Traction ID: {3}"
			return con_message.format(str(amount), COIN_NAME, self.address, trans_id)
		else:
			return "Insufficient Funds!"


# Routes
@app.route('/')
def index(): return get_index()

@app.route('/add', methods=['POST'])
def add(): 
	ip = str(request.remote_addr)
	try:
		captcha_try = hashlib.sha1(request.form['captcha']).hexdigest()
		if captcha_try != request.form['captcha_awns']: 
			raise ValueError
		print("Good drip request. Saving to database...")
		DripRequest(request.form['address'], request.form['coupon'], ip).save()
		return redirect(url_for('good'))
	except ValueError:
		print("Bad drip request. Redirecting...")
		return redirect(url_for('bad'))
	except LookupError:
		print("Duplicate IP or Address. Redirecting...")
		return redirect(url_for('duplicate'))
	else:
		print("Unexplained failure.")
		return redirect(url_for('bad'))

@app.route('/good')
def good(): 
	send_coins()
	return get_index("good")
@app.route('/bad')
def bad(): return get_index("bad")
@app.route('/duplicate')
def duplicate(): return get_index("duplicate")

@app.route('/chat')
def chat(): return render_template('chat.html')
@app.route('/resources')
def resources(): return render_template('resources.html')


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)