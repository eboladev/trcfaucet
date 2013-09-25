trcfaucet
========
A cryptocoin faucet webapp, developed in Python and [Flask](http://flask.pocoo.org/), a Python microframework for web. Front-end design was built with [Zerb Foundation](http://foundation.zurb.com/), and database used is [SQLite](https://www.sqlite.org/). Note that this is very roughly coded in a few weekends a technical prototype, and to help out new Terracoin users. If you try to use this code, note that probably run into many problems and bugs, although it could be used as a good reference for Bitcoin related webapps. 

Quick Overview
-------

In essence, the web-app gives the user a form which they can input their payment address, along with a very simple CAPTCHA. The user may also enter a coupon which will allow them a larger payout. The system then verifies this information, and anti-bot/spam/time limit measures are implemented. For example, the user can only request payment every certain number of minutes (this is to prevent bots that have made thousands of requests in the past). 

If the information is correct, then the request for a micropayment is stored in the SQLite database. An "always running" Python program checks the database ever few seconds for a new request. When it finds a new request it will make pass a command line argument to the coin client to send the micropayment to the user. 

This system has only been tested with the Terracoin client. All code seems to work just fine on a Debian 64-bit box with minimal specs. The coin's deamon must be kept running for the webapp to work correctly. 

Problems
-------
This is faucet is only intended to allow users to get a small amount of coins for testing as a community service. To that point there are glaring holes in the webapp that should probably be addressed with time or before public consumption. They are listed below in order of importance. 

1.  Rather than using the secure and recommended JSONRPC method the webapp passes payment requests directly to the coin client via command line. This leaves the app open to database injections where the attacker can gain access to the entire VPS. 
2.  CAPTCHA challenge is a simple math problem. Bots have found many ways to circumvent this and send hundreds of requests. This might be OK in the future simply to boost stats, but quickly drains the faucet balance w/ fees.
3.  The faucet gives out a very small amount of coin, but this still seems enough to entice people to use it. The faucet can pay 5x more than the actual microtransaction just on fees. SENDMANY needs to be implemented, and will allow many more transactions to take place. 
4.  For ease of development: Github hooks/automatic deployment would save a ton of time. Having the web-app be able to automatically manage the client/clients. Using an actually Python daemon library rather than a Python program running in an infinite loop.
5.  A method to reward user interaction and referrals. Traffic dips quite a bit if not directly supported by an advertising program. 
