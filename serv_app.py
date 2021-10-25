from flask import Flask, render_template 
from elasticsearch import Elasticsearch
import re, requests
from threading import *
from beebotte import *

I_WRITE = 0
# primera_vez = 1

elastic_client = Elasticsearch([{'host':'localhost','port':9200}])
token = 'token_5YNOoMGF3pj5EP1f'
hostname = 'api.beebotte.com'
bclient = BBT(token=token,hostname=hostname)
bbdd = Resource(bclient, 'cer_bbddserver','bbddserver')
app = Flask(__name__)

tabla = "tabla2"
elastic_client.indices.create(index=tabla, ignore=400)
elastic_client.indices.delete(index=tabla, ignore=[400,404])

@app.route("/")#,methods=['GET'])
def inicio():
    r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
    return render_template('index.html',num_aleat=r)

@app.route("/hello")
def hello():
    for i in range(I_WRITE):
        data = elastic_client.get(index=tabla,id=i)['_source']['numero']
        print(str(data))
    lectura = bbdd.read(limit=I_WRITE) # LEE TODA LA BASE DE DATOS DE INTERNET
    print(lectura)
    return render_template('/laura/index.html',num_aleat=str(data))


@app.route("/entrada")
def input():
    return 'entrada'
@app.route("/registro") 
def register():
    return 'registro'
@app.route("/media_local") 
def local_mean():
    return 'media_local'
@app.route("/media_internet") 
def internet_mean():
    return 'media_internet'    
@app.route("/graficas") 
def graphs():
    return 'graficas'    
    
def get_num_aleatorio():
    global I_WRITE
    while True: 
        r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
        elastic_client.index(index=tabla, id=I_WRITE, document={'numero':float(r)})
        bbdd.write(float(r),I_WRITE)
        I_WRITE =I_WRITE+1
        time.sleep(120)

if __name__ == "__main__":

    hilo1 = Thread(target=get_num_aleatorio, daemon=True)
    hilo1.start()
    app.run(host='0.0.0.0', port=5000, debug=True)