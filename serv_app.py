from flask import Flask, render_template 
from elasticsearch import Elasticsearch
import re, requests
from threading import *
from beebotte import *


I_WRITE = 0
# primera_vez = 1
login = True
medialocal_global = "No se puede obtener este valor sin estar registrado"
mediainternet_global = "No se puede obtener este valor sin estar registrado"

elastic_client = Elasticsearch([{'host':'localhost','port':9200}])
token = 'token_5YNOoMGF3pj5EP1f'
hostname = 'api.beebotte.com'
bclient = BBT(token=token,hostname=hostname)
recurso="bbddserver_1"
#bclient.deleteResource('cer_bbddserver', recurso)
#resource_bbdd = Resource(bclient,'cer_bbddserver',recurso)
# bclient.addResource(
#   channel = 'cer_bbddserver',
#   name = recurso,
#   vtype = BBT_Types.Number,
#   label = "Base de datos internet prueba",
#   description = "Base de datos de internet prueba",
#   sendOnSubscribe = False
# )
#bbdd = Resource(bclient, 'cer_bbddserver','bbddserver')
app = Flask(__name__)

tabla = "tabla2"
elastic_client.indices.create(index=tabla, ignore=400)
elastic_client.indices.delete(index=tabla, ignore=[400,404])

@app.route("/")
def inicio():
    r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
    return render_template('index.html',num_aleat=r, mean_local = medialocal_global, mean_beebotte=mediainternet_global)

@app.route("/hello")
def hello():
    print("Base de datos local")
    for i in range(I_WRITE):
        data = elastic_client.get(index=tabla,id=i)['_source']['numero']
        #print(str(data))
        print('Elemento '+str(i)+' : '+str(data)+'\n')
    #lectura = bbdd.read('cer_bbddserver','bbddserver',limit=I_WRITE) # LEE TODA LA BASE DE DATOS DE INTERNET
    # lectura = bbdd.read(limit=I_WRITE)
    # lectura = bclient.read('cer_bbddserver','bbddserver',limit=I_WRITE)
    print("Base de datos de internet")
    lectura = bclient.read('cer_bbddserver',recurso,limit=I_WRITE)
    print(lectura)
    return render_template('/laura/index.html',num_aleat=str(data), mean_local = medialocal_global, mean_beebotte=mediainternet_global)


@app.route("/entrada")
def input():
    return 'entrada'
@app.route("/registro") 
def register():
    return 'registro'
@app.route("/media_local") 
def local_mean():
    global medialocal_global
    data = []
    print("\nCalculo de la media en la base de datos local:")
    for i in range(I_WRITE):
        data.append(elastic_client.get(index=tabla,id=i)['_source']['numero'])
        print('Elemento '+str(i)+' : '+str(data)+'\n')
    # diccionario_bbdd = elastic_client.search(index=tabla)
    # print(str(diccionario_bbdd))
    def media(sum_values,num_values):
        return sum_values/num_values
        
    # def get_values(dict):
    #     acum = 0
    #     for i in range(len(dict['hits']['hits'])):
    #         value = dict['hits']['hits'][i]['_source']['numero']
    #         print(str(i)+' numero de la lista: '+str(value))
    #         acum = acum + value
    #     return acum, len(dict['hits']['hits'])
    def get_values(dict):
        acum = 0
        for i in range(len(dict)):
            value = dict[i]
            print(str(i)+' numero de la lista: '+str(value))
            acum = acum + value
        return acum, len(dict)

    sum_values, num_values = get_values(data)
    mean = media(sum_values,num_values)

    print('La media es:'+str(mean))
    print(sum_values)
    print(num_values)
    if login == True:
        medialocal_global = str(mean)
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], 
                                mean_local=medialocal_global,mean_beebotte=mediainternet_global)
    else:
        medialocal_global = "No se puede obtener este valor sin estar registrado"
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], 
                                mean_local=medialocal_global,mean_beebotte=mediainternet_global)

@app.route("/media_internet") 
def internet_mean():
    global mediainternet_global
    #lectura = bbdd.read(limit=I_WRITE) # LEE TODA LA BASE DE DATOS DE INTERNET
    # lectura = bclient.read('cer_bbddserver','bbddserver',limit=I_WRITE)
    lectura = bclient.read('cer_bbddserver',recurso,limit=I_WRITE)
    print(str(lectura))

    def media(sum_values,num_values):
        return sum_values/num_values
        
    def get_values(dict):
        print("\nCalculo de la media en la base de datos de internet")
        acum = 0
        for i in range(len(dict)):
            value = dict[i]['data']
            print('Elemento '+str(i)+' de la lista: '+str(value))
            acum = acum + value
        return acum, len(dict)

    sum_values, num_values = get_values(lectura)
    mean = media(sum_values,num_values)

    print('La media es:'+str(mean))
    print(sum_values)
    print(num_values)
    if login == True:
        mediainternet_global = str(mean)
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], mean_local=medialocal_global,
                                mean_beebotte=mediainternet_global)
    else:
        mediainternet_global = "No se puede obtener este valor sin estar registrado"
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], mean_local=medialocal_global,
                                mean_beebotte=mediainternet_global)
    # return 'media_internet'    
@app.route("/graficas") 
def graphs():
    return 'graficas'    

def get_num_aleatorio():
    global I_WRITE
    while True: 
        r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
        elastic_client.index(index=tabla, id=I_WRITE, document={'numero':float(r)})
        #bbdd.write('cer_bbddserver','bbddserver',ts=I_WRITE,data=float(r))
        #bbdd.write(ts=I_WRITE,data=float(r))
        #bclient.write('cer_bbddserver','bbddserver',ts=I_WRITE,data=float(r))
        bclient.write('cer_bbddserver',recurso,data=float(r))
        I_WRITE =I_WRITE+1
        time.sleep(30) #120

if __name__ == "__main__":

    hilo1 = Thread(target=get_num_aleatorio, daemon=True)
    hilo1.start()
    app.run(host='0.0.0.0', port=5000, debug=True)