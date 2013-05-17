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