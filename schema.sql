drop table if exists drip_request;
create table drip_request (
	id integer primary key autoincrement, 
	crdate string not null,
	ip string not null,
	address string not null,
	coupon string not null,
	trans_id string not null
);
insert into drip_request (id, crdate, ip, address, coupon, trans_id) 
values (null, datetime('now'), "69.87.160.3", 
		"1DarXYYGgvyHFQKZKsgUq676A9CK7D7FYa", "DOUBLEMONEY",
		"bf9433692129d60f10f47d391c5b8435fc3852d0cd7c1f19db62403c5df89b3f");
drop table if exists coupon_list;
create table coupon_list (
	id integer primary key autoincrement, 
	coup_type string not null,
	coup_value integer not null,
	max_use integer not null,
	access_key string not null
);
insert into coupon_list (id, coup_type, coup_value, max_use, access_key) 
values (null, 'SINGLE_USE', 0.001, 25, '31491de80d');