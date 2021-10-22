from flask import Flask, render_template 
from elasticsearch import Elasticsearch
import re, requests

elastic_client = Elasticsearch([{'host':'localhost','port':9200}])
#elastic_client.delete(index="tabla1", id='_all')
tabla = "tabla1"
for i in range(5):
    r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
    elastic_client.index(index=tabla, id=i, document={'numero':float(r)})
data = elastic_client.get(index=tabla,id=3)
print(str(data['_source']['numero']))
elastic_client.indices.refresh(index=tabla)
forma = 0
if forma ==0:
    diccionario_bbdd = elastic_client.search(index=tabla)
    print(str(diccionario_bbdd))
    def media(sum_values,num_values):
        return sum_values/num_values
        
    def get_values(dict):
        acum = 0
        for i in range(len(dict['hits']['hits'])):
            value = diccionario_bbdd['hits']['hits'][i]['_source']['numero']
            print(str(i)+' numero de la lista: '+str(value))
            acum = acum + value
        return acum, len(dict['hits']['hits'])

    sum_values, num_values = get_values(diccionario_bbdd)
    mean = media(sum_values,num_values)

    print('La media es:'+str(mean))
    print(sum_values)
    print(num_values)
else:
    diccionario_bbdd = elastic_client.search(index=tabla, filter_path=['hits.hits._source'])
    def media(sum_values,num_values):
        return sum_values/num_values
        
    def get_values(dict):
        acum = 0
        for i in range(len(dict['hits']['hits'])):
            value = diccionario_bbdd['hits']['hits'][i]['_source']['numero']
            print(str(i)+' numero de la lista: '+str(value))
            acum = acum + value
        return acum, len(dict['hits']['hits'])

    sum_values, num_values = get_values(diccionario_bbdd)
    mean = media(sum_values,num_values)

    print('La media es:'+str(mean))
    print(sum_values)
    print(num_values)


