apt-get update
apt-get -y install build-essential libboost-all-dev libssl-dev libdb-dev libdb4.8++-dev libglib2.0-dev
apt-get update
apt-get -y install git apt-file python3 screen sqlite3 python-setuptools python-flask
apt-get update
apt-file update

git clone https://github.com/terracoin/terracoin.git
cd ~/terracoin/src
make -f makefile.unix terracoind
cp terracoind /usr/bin/terracoind

mkdir /root/.terracoin/
echo "rpcuser=CHANGETHIS" >> /root/.terracoin/terracoin.conf
echo "rpcpassword=CHANGETHIS" >> /root/.terracoin/terracoin.conf

sleep 5
terracoind -daemon
terracoind getinfo
terracoind getbalance
terracoind getnewaddress

cd ~/
git clone https://github.com/super3/CryptoTap.git
cd ~/CryptoTap
python CryptoTap.py 80