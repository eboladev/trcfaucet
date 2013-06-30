apt-get update
apt-get -y install build-essential libboost-all-dev libdb5.1++-dev libssl-dev
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

terracoind -daemon