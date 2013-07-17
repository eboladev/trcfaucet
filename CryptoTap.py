import re
import sys
import sqlite3
import hashlib
from random import randint
from datetime import datetime

from flask import g
from flask import Flask
from flask import url_for
from flask import request
from flask import redirect
from flask import render_template
from contextlib import closing

import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler


# Global Configs ---------------------------------------------------------------
DATABASE_INIT = 'schema.sql'

# Load Flask -------------------------------------------------------------------
app = Flask(__name__)
#app.config.from_object(__name__)
app.config.from_pyfile('settings.cfg')


# Database Functions -----------------------------------------------------------
def connect_db():
	return sqlite3.connect(app.config['DATABASE_FILE'])

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	if hasattr(g, 'db'):
		g.db.close()

def init_db():
	with closing(connect_db()) as db:
		with app.open_resource(app.config['DATABASE_INIT'], mode='r') as f:
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
		text = '{0} {1} {2} {3}'
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
		last_request(val)

	def save_db(self):
		"""Insert object data into database."""
		query = "INSERT INTO drip_request"
		query += "(id, crdate, ip, address, coupon, trans_id)"
		query += "VALUES (NULL, datetime('now','localtime'), ?, ?, ?, ?)"
		g.db.execute(query, (self.ip, self.address, self.coupon, "UNSENT",))
		g.db.commit()

	def save(self):
		"""Save drip request into database."""
		num_ip = self.count_unique("ip", self.ip)
		num_address = self.count_unique("address", self.address)
		last_req = last_request(self.ip)
		app.logger.debug("last_req:" + str(last_req))

		if self.address == '12Ai7QavwJbLcPL5XS276fkYZpXPXTPFC7':
			self.save_db()
		elif last_req >= app.config['REQUEST_TIME_LIMIT']:
			app.logger.info('Last Submit Time: '.format(last_req))
			self.save_db()
		else: # last_req < 60
			print(last_req)
			self.time_left = app.config['REQUEST_TIME_LIMIT'] - last_req
			raise LookupError("Last request less than 60 mins ago.")

		return self

	def send(self):
		return(self.address, self.coupon)


# Helper Functions -------------------------------------------------------------
def last_request(ip):
	"""Return the number of minutes since the last drip request."""
	query = "SELECT * FROM drip_request WHERE ip=? ORDER BY id DESC"
	req_date = g.db.execute(query, (ip,)).fetchone()
	#app.logger.debug(req_date)
	if req_date == None:
		return int(app.config['REQUEST_TIME_LIMIT'] + 1)
	else:
		req_datetime = datetime.strptime(req_date[1], "%Y-%m-%d %H:%M:%S")
		diff_time = datetime.now() - req_datetime
		diff_time = divmod(diff_time.total_seconds(), 60)
		return int(diff_time[0]) # minutes since last request

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
	diff_time = divmod(diff_time.total_seconds(), 60)
	diff_time = "{0} mins, {1} secs ago".format(int(diff_time[0]), int(diff_time[1]))
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
	# generate and hash the captcha
	captcha_raw = (randint(1, 15), randint(1, 15))
	captcha = str(int(captcha_raw[0] + captcha_raw[1])).encode('utf-8')
	captcha_hash = hashlib.sha1(captcha).hexdigest()

	# retrieve last drip requests
	query = 'SELECT * FROM drip_request ORDER BY id DESC LIMIT 10'
	recent = g.db.execute(query)
	recent = [get_html(row[1], row[2], row[5]) for row in recent.fetchall()]
	recent = ''.join(map(str, recent))

	# find total nunber of transactions
	cur = g.db.execute('SELECT Count(*) FROM drip_request')
	total_trans = app.config['TOTAL_TRANS'] + int(cur.fetchone()[0])
	stats = "{:,}".format(total_trans)

	# find time since last drip request
	last_req = app.config['REQUEST_TIME_LIMIT'] - last_request(str(request.remote_addr))

	# pass all data to the template for rendering
	return render_template('index.html', recent=recent,
						   form_submit=form_submit_status,
						   captcha_x=captcha_raw[0], captcha_y=captcha_raw[1],
						   captcha_awns=captcha_hash, stats=stats,
						   last_req=last_req)

def get_coupons_html(access_key, coup_value, max_use):
	html = "<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>"
	return html.format(access_key, coup_value, max_use)

def get_coupons():
	query = 'SELECT * FROM coupon_list'
	coupons = g.db.execute(query)
	coupons = [get_coupons_html(row[3], row[1], row[2]) for row in coupons.fetchall()]
	coupons = ''.join(map(str, coupons))
	return render_template('coupons.html', coupons=coupons)

# Routes -----------------------------------------------------------------------
@app.route('/')
def index(): return get_index()
@app.route('/add', methods=['POST'])
def add():
	# grab data
	ip = str(request.remote_addr)
	address = request.form['address']
	coupon = request.form['coupon']

	try:
		# convert user submitted captcha to an sha-1 hash
		# since the captcha is passed through a hidden input we need to obscure
		# the answer from the user. we do this by hashing the solution. 
		captcha = str(request.form['captcha']).encode('utf-8')
		captcha_user = hashlib.sha1(captcha).hexdigest()
		captcha_awn = request.form['captcha_awns']
		# compare sha-1 hash of correct captcha and user submitted solution
		if not captcha_user == captcha_awn: 
			app.logger.info('Invalid Captcha from {0}'.format(ip))
			raise ValueError("Invalid captcha")
		# TODO: salting also needs to be added as the user could simply modify
		# the html and insert a hash they know the answer to

		# create a drip request object. the constructor will validate the
		# input before adding the drip request to the database
		drip = DripRequest(address, coupon, ip)
		app.logger.info("Good drip: {0}".format(drip.save()))

		return redirect(url_for('good'))

	except ValueError as e:
		app.logger.info("Bad Address: {0} from {1}".format(address, ip))
		app.logger.info("Error Detail: {0}".format(e))
		return redirect(url_for('bad'))
	except LookupError as e:
		app.logger.info("Duplicate Address: {0} from {1}".format(address, ip))
		app.logger.info("Error Detail: {0}".format(e))
		return redirect(url_for('duplicate'))

	except:
		# ValueError and LookupError are raised on purpose, all other 
		# errors  should be considered logical bugs
		app.logger.error("Unexplained Error: {0}".format(sys.exc_info()[0]))
		return redirect(url_for('bad'))

# submission result pages
@app.route('/good')
def good(): return get_index("good")
@app.route('/bad')
def bad(): return get_index("bad")
@app.route('/duplicate')
def duplicate(): return get_index("duplicate")

# static pages
@app.route('/forum')
def forum(): return render_template('forum.html')
@app.route('/resources')
def resources(): return render_template('resources.html')
@app.route('/guide')
def guide(): return render_template('guide.html')

# admin pages
@app.route('/coupon123')
def coupon123(): return get_coupons()


# Main -------------------------------------------------------------------------
if __name__ == '__main__':
	# logging
	handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'))
	app.logger.addHandler(handler)
	# debug web server
	app.run(host='0.0.0.0', port=5000, debug=True)