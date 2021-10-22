from flask import Flask, render_template 
from beebotte import *
import re, requests

_token = 'token_2qsoQ03Mz00aL6nF'
_hostname = 'api.beebotte.com'
#bclient = BBT("API_KEY", "SECRET_KEY")
bclient = BBT(token=_token,hostname=_hostname)
# Remember that persistent data MUST be associated to an existing resource.
## Create a Resource object
bbdd = Resource(bclient, 'cer_pruebabbdd','bbdd')
## Write to the resource
for i in range(10):
    r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
    bbdd.write(float(r),i) #bbdd.write('cer_pruebabbdd','bbdd',(float(r))
    time.sleep(1)
lectura = bbdd.read(limit=740) 
print(lectura[0]['data'])
