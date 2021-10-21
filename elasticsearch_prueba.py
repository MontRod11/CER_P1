from flask import Flask, render_template 
from elasticsearch import Elasticsearch
import re, requests

elastic_client = Elasticsearch(hosts=["localhost"])
for i in range(5):
    r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
    elastic_client.index(index='tabla1', id=i, document={'numero':float(r)})


data = elastic_client.get(index="tabla1",id=3)
print(str(data['_source']['numero']))
diccionario_bbdd = elastic_client.search(index='tabla1')
print(diccionario_bbdd['hits']['hits']['_source']['numero'])
def media():
    values = diccionario_bbdd['_source']['numero']
