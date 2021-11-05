apt update && apt upgrade -y
apt install -y python3 
apt install -y python3-pip
pip3 install -r requirements.txt
echo 'export PATH="/home/$USER/.local/bin:$PATH"' >> .bashrc
source .bashrc
apt install -y curl
#source .bashrc
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-7.x.list
apt update
apt install -y elasticsearch
# apt install -y systemd
/etc/init.d/elasticsearch start
#pip install elasticsearch
#pip install beebotte