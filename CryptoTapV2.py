from flask import Flask
from DripRequest import *
from random import randrange
from flask import render_template
app = Flask(__name__)

# TODO:
# Improve Captcha Security with Sha Hashing
# Improve IP Address Obfuscation
# Don't Make a Transaction If Balance is Low
# Revamp Coupon System

# Globals
DATABASE_FILE = 'trc.db'
DATABASE_TABLE = 'drip_request'
DEFAULT_SEND_VAL = 0.0001

# Helper Functions
def sub_cypher(num, offset):
	"""Number substitution offset cypher. Don't use offset values 0-9."""
	# Implement Better Cypher: rotate((ip % sum1bits(ip) ), sum0bits(ip))
	return [(abs(int(x) - offset)%10) if x.isdigit() else '.' for x in num]

def get_html(save_time, ip, trans_id):
	"""Transform database output into a table."""
	obfuscated_ip = ''.join(map(str, sub_cypher(list(ip), 655)))

	if trans_id == "UNSENT":
		html = "<tr><td>{0}</td><td>{1}</td><td>Processing...</td></tr>"
	else:
		short_trans_id = trans_id[:40]
		trans_id_url = "http://cryptocoinexplorer.com:3750/tx/{0}".format(trans_id)
		html = "<tr><td>{0}</td><td>{1}</td><td><a href='{2}'>{3}</a></td></tr>"
		html = html.format(save_time, obfuscated_ip, trans_id, short_trans_id)
	
	return html

def get_index(form_submit_status = None):
	"""Displays the default index page, or a success/error page."""
	captcha = (randrange(1, 15), randrange(1, 15))no
	captcha_awns = captcha[0] + captcha[1]
	recent_drips = Database(DATABASE_FILE, DATABASE_TABLE).get_recent()
	recent_drips_html = [get_html(x[1], x[2], x[5]) for x in recent_drips if True]
	recent = ''.join(map(str, recent_drips_html))
	return render_template('index.html', recent=recent, form_submit=form_submit_status,
						   captcha=captcha, captcha_awns=captcha_awns)

def send_coins():
	"""Sends queued coins."""
	data = Database(DATABASE_FILE, DATABASE_TABLE)
	for i in data.get_unsent():
		DripRequest(i[1], i[3], i[4], i[2], i[0]).send(DEFAULT_SEND_VAL, data)
	return "Sent!"

# Routes
@app.route('/')
def index():
	return get_index()

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80, debug=True)