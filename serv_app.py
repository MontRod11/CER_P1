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
    # global I_WRITE
    # global primera_vez
    #if primera_vez == 1:
    #     r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
    #     elastic_client.index(index=tabla, id=I_WRITE, document={'numero':float(r)})
    #     bbdd.write(float(r),I_WRITE)
    #     I_WRITE =I_WRITE+1
    #     primera_vez = 0
    # else:
    #     r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
    r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
    return render_template('index.html',num_aleat=r)

@app.route("/hello")
def hello():
    #global i_write
    for i in range(I_WRITE):
        data = elastic_client.get(index=tabla,id=i)['_source']['numero']
        print(str(data))
    lectura = bbdd.read(limit=I_WRITE) # LEE TODA LA BASE DE DATOS DE INTERNET
    print(lectura)
    return render_template('/laura/index.html',num_aleat=str(data))

def get_num_aleatorio():
    global I_WRITE
    while True: 
        r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
        elastic_client.index(index=tabla, id=I_WRITE, document={'numero':float(r)})
        bbdd.write(float(r),I_WRITE)
        I_WRITE =I_WRITE+1
        time.sleep(120)
    # diccionario_bbdd = elastic_client.search(index=tabla)
    # print(str(diccionario_bbdd['hits']['hits']))
    # value = diccionario_bbdd['hits']['hits'][i]['_source']['numero']
    # print(str(value))
    #return render_template('index.html',num_aleat=str(data))

# def num_aleatorio():
#     global i_write

#     for i in range(i_write):
#         data = elastic_client.get(index=tabla,id=i)['_source']['numero']
#         print(str(data))
#     # diccionario_bbdd = elastic_client.search(index=tabla)
#     # print(str(diccionario_bbdd['hits']['hits']))
#     # value = diccionario_bbdd['hits']['hits'][i]['_source']['numero']
#     # print(str(value))
#     return render_template('index.html',num_aleat=str(data))
#@app.route("/laura")
#def hello_laura():
#    return render_template('/laura/index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4])
# hilo1 = Timer(120,get_num_aleatorio)#Thread(target=get_num_aleatorio)

if __name__ == "__main__":

    # for i in range(5):
    #     r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
    #     elastic_client.index(index=tabla, id=i, document={'numero':float(r)})
    #     i_write =i_write+1
    #app.run()
    hilo1 = Thread(target=get_num_aleatorio, daemon=True)
    hilo1.start()
    app.run(host='0.0.0.0', port=5000, debug=True)