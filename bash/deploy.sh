rm -rf ~/trcfaucet
git clone https://github.com/super3/trcfaucet.git
cd ~/trcfaucet/
#python CryptoTap.py
gunicorn -w 3 -b 0.0.0.0:80  CryptoTap:app