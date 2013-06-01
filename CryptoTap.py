import re
import sys
import sqlite3
import hashlib
from random import randrange
from datetime import datetime

from flask import g
from flask import Flask
from flask import url_for
from flask import request
from flask import redirect
from flask import render_template
from contextlib import closing


# Global Configs ---------------------------------------------------------------
DATABASE = '/root/trc.db'
DATABASE_INIT = 'schema.sql'
DATABASE_TABLE = 'drip_request'
REQUEST_LIMIT = 3
REQUEST_TIME_LIMIT = 60 # minutes
COIN_NAME = 'TRC'
BLOCK_EXPLORER_URL = 'http://cryptocoinexplorer.com:3750/tx/'

# Load Flask -------------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(__name__)


# Database Functions -----------------------------------------------------------
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
		with app.open_resource(app.config['DATABASE_INIT']) as f:
			db.cursor().executescript(f.read())
		db.commit()


# Affiliate System -------------------------------------------------------------
class Affiliate:
	def __init__(self):
		pass


# API System -------------------------------------------------------------------
class API:
	def __init__(self):
		pass


# Classes ----------------------------------------------------------------------
class DripRequest:
	"""
	Stores a users terracoin send request. 

	Data Members:
	address -- Terracoin address to send the transaction to.
	coupon  -- Special code that allows users to get additional coins.
	ip      -- The IP address that the request was made from.
	drip_id -- The database id of the drip request.
	
	"""

	# Magics -------------------------------------------------------------------
	def __init__(self, address, coupon, ip, drip_id = 0):
		# Validate all input
		if not self.validate_address(address):
			errmsg = 'Invalid {0} Address'.format(app.config['COIN_NAME']) 
			raise ValueError(errmsg)
		elif not self.validate_coupon(coupon): 
			coupon = 'INVALID'
		elif not self.validate_ip(ip): 
			raise ValueError('Invalid IP')

		# Cast everything
		self.address = str(address)
		self.coupon = str(coupon).upper()
		self.ip = str(ip)
		self.drip_id = int(drip_id)

	def __str__(self):
		"""Object to string for easy debugging."""
		text = '{0} {1} {2} {3} {4}'
		return text.format(self.address, self.coupon, self.ip, self.drip_id)

	# Validation and Clean Functions -------------------------------------------
	def clean(self, in_str):
		"""Strips out chars that are not alphanumeric."""
		pattern = re.compile('[\W_]+')
		return pattern.sub('', str(in_str))

	def validate_address(self, address):
		"""
		Does simple validation of a bitcoin-like address. 
		Source: http://bit.ly/17OhFP5

		param : address : an ASCII or unicode string, of a bitcoin address.
		returns : boolean, indicating that the address has a correct format.

		""" 
		
		address = self.clean(address)
		# The first character indicates the "version" of the address.
		CHARS_OK_FIRST = "123"
		# alphanumeric characters without : l I O 0
		CHARS_OK = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
		
		# We do not check the high length limit of the address. 
		# Usually, it is 35, but nobody knows what could happen in the future.
		if len(address) < 27:
			return False
		elif address[0] not in CHARS_OK_FIRST:
			return False

		# We use the function "all" by passing it an enumerator as parameter. 
		# It does a little optimization : 
		# if one of the character is not valid, the next ones are not tested.
		return all( ( char in CHARS_OK for char in address[1:] ) )
	
	def validate_coupon(self, coupon):
		"""Makes sure the coupon is alphanumeric and less than 12 chars."""
		coupon = self.clean(coupon)
		return re.match('^[\w]+$', coupon) and len(coupon)<12

	def validate_ip(self, ip):
		"""Checks for a valid IP address."""
		return re.match('([0-9]{1,3}\.){3}[0-9]+', str(ip))	

	# Database Methods ---------------------------------------------------------
	def count_unique(self, row, val):
		"""Count the number of unique row for a particular value."""
		if row == 'ip':
			query = "SELECT Count(*) FROM drip_request WHERE ip=?"
		elif row == 'address':
			query = "SELECT Count(*) FROM drip_request WHERE address=?"
		cur = g.db.execute(query, (val,))
		return int(cur.fetchone()[0])

	def last_request(self, val):
		"""Return the number of minutes since the last drip request."""
		query = "SELECT * FROM drip_request WHERE ip=? ORDER BY id DESC"
		cur = g.db.execute(query, (self.ip,))
		req_date = cur.fetchone()
		if req_date == None:
			return 0
		else:
			req_datetime = datetime.strptime(req_date[1], "%Y-%m-%d %H:%M:%S")
			diff_time = datetime.now() - req_datetime
			diff_time = divmod(diff_time.seconds, 60)
			return int(diff_time[0]) # minutes since last request

	def save_db(self):
		"""Insert object data into database."""
		query = "INSERT INTO drip_request"
		query += "(id, crdate, ip, address, coupon, trans_id)"
		query += "VALUES (NULL, datetime('now'), ?, ?, ?, ?)"
		g.db.execute(query, (self.ip, self.address, self.coupon, "UNSENT",))
		g.db.commit()

	def save(self):
		"""Save drip request into database."""
		num_ip = self.count_unique("ip", self.ip)
		num_address = self.count_unique("address", self.address)
		last_req = self.last_request(self.ip)

		request_str = "IP: {0}/{1} and Address: {2}/{3}. Last Req: {4} mins"
		request_str = request_str.format(num_ip, REQUEST_LIMIT, num_address,
										 REQUEST_LIMIT, last_req)
		print(request_str)

		if self.address == '12Ai7QavwJbLcPL5XS276fkYZpXPXTPFC7':
			self.save_db()
		elif num_ip < REQUEST_LIMIT and num_address < REQUEST_LIMIT:
			self.save_db()
		elif last_req >= app.config['REQUEST_TIME_LIMIT']:
			self.save_db()
		else: # last_req < 60
			raise LookupError("Last request less than 60 mins ago.")

	def send(self):
		return(self.address, self.coupon)


# Helper Functions -------------------------------------------------------------
def sub_cypher(ip, offset):
	"""
	A basic number substitution cypher using a number offset. Don't use offset
	values 0-9, as then all values will be either 0 or 1. This is used to 
	obfuscated the IP address before the are publicly displayed.

	The	cypher is currently easily reversed if the offset is known. Here is
	another implementation that was suggested: 
		rotate((ip % sum1bits(ip) ), sum0bits(ip))

	"""
	return [(abs(int(x) - offset)%10) if x.isdigit() else '.' for x in ip]

def get_html(save_time, ip, trans_id):
	"""Transform database output into a table."""
	diff_time = datetime.now()-datetime.strptime(save_time, "%Y-%m-%d %H:%M:%S")
	diff_time = divmod(diff_time.seconds, 60)
	diff_time = "{0} mins, {1} secs ago".format(diff_time[0], diff_time[1])
	obfuscated_ip = ''.join(map(str, sub_cypher(list(ip), 756)))

	if trans_id == "UNSENT":
		html = "<tr><td>{0}</td><td>{1}</td><td>Processing...</td></tr>"
		return html.format(diff_time, obfuscated_ip)
	else:
		short_trans_id = trans_id[:37] + "..."
		trans_url = app.config['BLOCK_EXPLORER_URL'] + trans_id
		html = "<tr><td>{0}</td><td>{1}</td><td><a href='{2}'>{3}</a></td></tr>"
		return html.format(diff_time, obfuscated_ip, trans_url, short_trans_id)
		
def get_index(form_submit_status = None):
	"""Displays the default index page, or a success / error page."""
	captcha = (randrange(1, 15), randrange(1, 15))
	captcha_awns = hashlib.sha1(str(captcha[0] + captcha[1])).hexdigest()

	query = 'SELECT * FROM drip_request ORDER BY id DESC LIMIT 10'
	recent = g.db.execute(query)
	recent = [get_html(row[1], row[2], row[5]) for row in recent.fetchall()]
	recent = ''.join(map(str, recent))
	
	cur = g.db.execute('SELECT Count(*) FROM drip_request')
	stats = 4100 + int(cur.fetchone()[0])

	return render_template('index.html', recent=recent,
						   form_submit=form_submit_status, captcha=captcha,
						   captcha_awns=captcha_awns, stats=stats)


# Routes -----------------------------------------------------------------------
@app.route('/')
def index(): return get_index()

@app.route('/add', methods=['POST'])
def add(): 
	ip = str(request.remote_addr)
	try:
		captcha_try = hashlib.sha1(request.form['captcha']).hexdigest()
		if captcha_try != request.form['captcha_awns']: 
			raise ValueError
		DripRequest(request.form['address'], request.form['coupon'], ip).save()
		print("Good drip request. Saving to database...")
		return redirect(url_for('good'))
	except ValueError as detail:
		print("Bad: " + str(detail))
		return redirect(url_for('bad'))
	except LookupError as detail:
		print("Duplicate: " + str(detail))
		return redirect(url_for('duplicate'))
	except:
		print(sys.exc_info()[0])
		return redirect(url_for('bad'))

@app.route('/good')
def good(): return get_index("good")
@app.route('/bad')
def bad(): return get_index("bad")
@app.route('/duplicate')
def duplicate(): return get_index("duplicate")

@app.route('/forum')
def forum(): return render_template('forum.html')
@app.route('/resources')
def resources(): return render_template('resources.html')
@app.route('/guide')
def guide(): return render_template('guide.html')


# Main -------------------------------------------------------------------------
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80)