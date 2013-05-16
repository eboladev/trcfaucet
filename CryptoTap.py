import web
import random
import datetime
from DripRequest import *

DATABASE_FILE = 'trc.db'
DATABASE_TABLE = 'drip_request'
DEFAULT_SEND_VAL = 0.0001

urls = (
	'/', 'index',
	'/add', 'add',
	'/good', 'good',
	'/bad', 'bad',
	'/duplicate', 'duplicate',
	'/send', 'send',
	'/chat', 'chat',
	'/resources', 'resources'
)

def sub_cypher(num, offset):
	"""Number substitution offset cypher. Don't use offset values 0-9."""
	return [(abs(int(x) - offset)%10) for x in num if x.isdigit()]

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
	render = web.template.frender('index.html')
	captcha = (random.randrange(1, 15), random.randrange(1, 15))
	captcha_awns = captcha[0] + captcha[1]
	recent_drips = Database(DATABASE_FILE, DATABASE_TABLE).get_recent()
	recent_drips_html = [get_html(x[1], x[2], x[5]) for x in recent_drips if True]
	recent_drips_html = '.'join(map(str, recent_drips_html)
	return render(recent_drips_html, form_submit_status, captcha, captcha_awns)

def send_coins():
	"""Sends queued coins."""
	data = Database(DATABASE_FILE, DATABASE_TABLE)
	for i in data.get_unsent():
		DripRequest(i[1], i[3], i[4], i[2], i[0]).send(DEFAULT_SEND_VAL, data)
	return "Sent!"

class add:
	"""Takes add POST request, and redirects to relevant page"""
	def POST(self):
		i = web.input()
		ip = str(web.ctx.get('ip'))
		now = str(datetime.datetime.now())
		try:
			if i.captcha != i.captcha_awns: raise ValueError
			print("Good drip request. Saving to database...")
			data = Database(DATABASE_FILE, DATABASE_TABLE)
			DripRequest(now, i.address, i.coupon, ip).save(data)
			raise web.seeother('/good')
		except ValueError:
			print("Bad drip request. Redirecting...")
			raise web.seeother('/bad')
		except LookupError:
			print("Duplicate IP or Address. Redirecting...")
			raise web.seeother('/duplicate')
		else:
			print("Unexplained failure.")
			raise web.seeother('/bad')

# Unfortunately, web.py does not allow me to route to functions, so
# this will always look a bit messy in my opinion. 

class index:
	"""Displays index page."""
	def GET(self): return get_index()

class good:
	"""Displays success page."""
	def GET(self):
		#send_coins()
		return get_index("good")

class bad:
	"""Displays error page."""
	def GET(self): return get_index("bad")

class duplicate:
	"""Displays duplicate page."""
	def GET(self): return get_index("duplicate")

class send:
	"""Sends unprocessed drips."""
	def GET(self): return send_coins()

# Other pages.

class chat:
	def GET(self): return web.template.frender('chat.html')()

class resources:
	def GET(self): return web.template.frender('resources.html')()


if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()