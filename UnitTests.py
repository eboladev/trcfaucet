from CryptoTap import API
from SendCoin import Coupon
from CryptoTap import Affliate
from CryptoTap import DripRequest

# Sample Addresses
assert(drip.validate_address("1aueAUEZMN9875bjnsYXYX52366ZMWJJ"))
assert(not drip.validate_address("1aueAUEZMN9875bjnsYXYX52366ZMWJJO"))
assert(drip.validate_address("3aueAUEZMN9875bjnsYXYX52366ZMWJJio1L"))
assert(not drip.validate_address(""))
assert(not drip.validate_address("1"))
assert(not drip.validate_address("4aueAUEZMN9875bjnsYXYX52366ZMWJJ"))

# Sample Coupons
assert(drip.validate_coupon("DOUBLEMONEY"))
assert(drip.validate_coupon("MOREMONEY"))
assert(not drip.validate_coupon("NOTCOUPON"))
assert(not drip.validate_coupon("WAYTOOLONGCOUPON"))
assert(not drip.validate_coupon("<?echo 'H';?>"))
assert(not drip.validate_coupon("<div><div>"))
assert(not drip.validate_coupon("</div></div>"))

# Sample IPs
assert(not drip.validate_ip("notiplol"))
assert(drip.validate_ip("69.87.160.3"))