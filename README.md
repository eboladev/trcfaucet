Install
=========
apt-get update
apt-get -y install build-essential libboost-all-dev libssl-dev libdb-dev libdb4.8++-dev libglib2.0-dev
apt-get -y install git apt-file python3 python-webpy 
apt-get update

git clone https://github.com/terracoin/terracoin.git
git clone https://github.com/super3/CryptoTap.git

cd ~/terracoin/src
make -f makefile.unix terracoind
echo "rpcuser=trcfaucet1" >> /root/.terracoin/terracoin.conf
echo "rpcpassword=R&0&Jij0YHBW2&g6zGn5zwiTpY8$7yd%q4Gm" >> /root/.terracoin/terracoin.conf

cp terracoind ~/CryptoTap
cd ~/CryptoTap
./terracoind -daemon
python CryptoTap.py 80

Re-Deploy CryptoTap
=========
cd ~/
rm -rf ~/CryptoTap
git clone https://github.com/super3/CryptoTap.git
cd ~/CryptoTap
cp ~/terracoin/src/terracoind terracoind