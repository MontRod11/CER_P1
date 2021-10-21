apt update && apt upgrade -y
apt install python3-pip
pip3 install -r requirements.txt
echo 'export PATH="/home/$USER/.local/bin:$PATH""' >> .bashrc
source .bashrc
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list
apt update
apt install -y elasticsearch