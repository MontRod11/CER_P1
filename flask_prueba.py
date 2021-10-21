from flask import Flask, render_template 
from elasticsearch import Elasticsearch
import re, requests
app = Flask(__name__)

@app.route("/")
def num_aleatorio():
    return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4])
@app.route("/hello")
def hello():
    return render_template('/laura/index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4])

@app.route("/laura")
def hello_laura():
    return render_template('/laura/index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4])
if __name__ == "__main__":
    
    #app.run()
    app.run(host='0.0.0.0', port=5000, debug=True)