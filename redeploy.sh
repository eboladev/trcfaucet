cd ~/
rm -rf ~/CryptoTap
git clone https://github.com/super3/CryptoTap.git
cd ~/CryptoTap
cp ~/terracoin/src/terracoind terracoind
./terracoind -daemon
python CryptoTap.py 80