from flask import Flask, render_template, redirect, request,session
from elasticsearch import Elasticsearch
import re, requests, uuid, hashlib, time
from flask.helpers import total_seconds
from threading import Thread
from beebotte import *


I_WRITE = 0
I_WRITE_NAMES = 0
login_var = False
user = "Inicie sesión"
medialocal_global = "No se puede obtener este valor sin estar registrado"
mediainternet_global = "No se puede obtener este valor sin estar registrado"
bad_pass = 0
ya_registrado = 0
# CREAR NUEVO RECURSO CADA VEZ, SE PUEDE HACER USANDO EL CÓDIGO COMENTADO SI SE PONE LA API Y SECRET KEY

elastic_client = Elasticsearch([{'host':'localhost','port':9200}])
token = 'token_5YNOoMGF3pj5EP1f'
hostname = 'api.beebotte.com'
bclient = BBT(token=token,hostname=hostname)
recurso="bbddserver_2"
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

app = Flask(__name__)
app.secret_key = 'lausi'

tabla = "tabla2"
elastic_client.indices.create(index=tabla, ignore=400)
elastic_client.indices.delete(index=tabla, ignore=[400,404])
tabla_nombres = "tabla_nombres1"
elastic_client.indices.create(index=tabla_nombres, ignore=400)

@app.route("/")#,methods = ["POST"])
def inicio():
    """
    Esta función es la funcion base e inicial del programa, en este caso solo se actualiza el indice sacando un número aleatorio de la pagina web numero al azar
    """
    r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
    return render_template('index.html',num_aleat=r, mean_local = medialocal_global, mean_beebotte=mediainternet_global, user=user)


@app.route("/hello")
def hello():
    """ 
    Esta funcion es una función de prueba que permite ver en la terminal las bases de datos y sus contenidos y muestra en el índice el último elemento que se
    ha incluido en la base de datos local.
    """
    print("\nBase de datos local")
    for i in range(I_WRITE):
        data = elastic_client.get(index=tabla,id=i)['_source']['numero']
        print('Elemento '+str(i)+' : '+str(data))

    print("Base de datos de internet")
    lectura = bclient.read('cer_bbddserver',recurso,limit=I_WRITE)
    for i in range(len(lectura)):
        value = lectura[i]['data']
        print('Elemento '+str(i)+' : '+str(value))
    print('\n')
    return render_template('/laura/index.html',num_aleat=str(data), mean_local = medialocal_global, mean_beebotte=mediainternet_global, user=user)


@app.route("/login")
def login():
    """Realizar el login"""
    return render_template("indexlogin.html")  

@app.route("/loggeado",methods = ["POST"])
def loggeado():
    global I_WRITE_NAMES
    global login_var
    global user
    global bad_pass
    # if bad_pass == 1:
    #   user_prev = '0'
    # else:
    #   user_prev = user
    user_prev = user
    if request.method == "POST":  
        user=request.form['email'] 
        password = request.form['pass']
        if user == '':
	        return render_template('falloiniciosesion.html')	
        else:
            if user == user_prev:# and bad_pass != 1:
                return render_template('falloinicio_logged.html')
            if I_WRITE_NAMES == 0:
                """Devolver nuevo index donde se indique que no está registrado"""
                user = ''
                return render_template('falloiniciosesionnosignin.html')
            else:
                for i in range(I_WRITE_NAMES):
                    nombre = elastic_client.get(index=tabla_nombres,id=i)['_source']['nombre']
                    passkey = elastic_client.get(index=tabla_nombres,id=i)['_source']['password']
                    print('Nombre '+str(i)+' : '+nombre)
                    if (nombre == user) and (password == passkey):
                        session['username'] = user
                        """ Inicio de sesión:
                            - Comprobar contraseña
                            - Devolver el index con la sesión iniciada
                        """
                        login_var = True
                        r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
                        return render_template('index.html',num_aleat=r, mean_local = medialocal_global, mean_beebotte=mediainternet_global, user=user)
                    elif (nombre == user) and (password != passkey):
                        bad_pass = 1
                        return render_template('indexlogin_badpass.html')
                    else:
                        """Devolver nuevo index donde se indique que no está loggeado"""
                        return render_template('falloiniciosesionnosignin.html')


@app.route("/signin")  
def signin():
    """Realizar el signin metiendo el ususario en la base de datos y usandolo como inicio de sesion"""
    return render_template("indexsignin.html")  

@app.route("/registrado",methods = ["POST"])
def registrado():
    """Comprobar que existe el usuario en la base de datos y comprobar la constaseña devolver en user el session['email'] ya que es un str """
    global I_WRITE_NAMES
    global ya_registrado
    # global user
    if request.method == "POST":  
        user_reg=request.form['email'] 
        password = request.form['pass']
        if user_reg == '':
	        return render_template('falloregistro.html')	
        else:
            if I_WRITE_NAMES == 0:
                salt=  uuid.uuid4().hex # Fuente: https://www.iteramos.com/pregunta/44612/la-sal-y-el-hash-de-una-contrasena-en-python
                # contraseña cifrada con la sal, elegida porque más segura que semilla
                # passw =  hashlib.sha512(password.encode('utf-8') + salt.encode('utf-8')).hexdigest() #Fuente: https://www.iteramos.com/pregunta/44612/la-sal-y-el-hash-de-una-contrasena-en-python
                passw =  hashlib.sha512(password + salt).hexdigest()
                elastic_client.index(index=tabla_nombres, id=I_WRITE_NAMES, document={'nombre':user_reg,'password':passw,'sal':salt})
                I_WRITE_NAMES =I_WRITE_NAMES+1
                return render_template('indexlogin.html')
                #return render_template('index.html',mean_local = medialocal_global, mean_beebotte=mediainternet_global, user=user)
            else:
                for i in range(I_WRITE_NAMES):
                    nombre = elastic_client.get(index=tabla_nombres,id=i)['_source']['nombre']
                    print('Nombre '+str(i)+' : '+nombre)
                    if nombre == user_reg:
                        ya_registrado = 1
                if ya_registrado == 1:
                    ya_registrado = 0
                    return render_template('falloregistro_yaloggeado.html')
                else:
                    salt = uuid.uuid4().hex # semilla con la que se va a cifrar 
                    passw = hashlib.sha512(password + salt).hexdigest()
                    elastic_client.index(index=tabla_nombres, id=I_WRITE_NAMES, document={'nombre':user_reg,'password':passw,'sal':salt})
                    I_WRITE_NAMES =I_WRITE_NAMES+1
                    return render_template('indexlogin.html')
    

@app.route("/logout") 
def logout():
    global login_var
    global medialocal_global
    global mediainternet_global
    global user
    session.pop(user,None)
    user = "Inicie Sesión"
    login_var = False
    mediainternet_global = "No se puede obtener este valor sin estar registrado"
    medialocal_global = "No se puede obtener este valor sin estar registrado"
    return render_template("indexlogout.html") 

@app.route("/media_local") 
def local_mean():
    """
    Esta función realiza el cálculo de la media de la base de datos local y actualiza la página web sacando su valor, si el usuario está loggeado y, si no lo 
    está, entonces no saca nada.
    """
    global medialocal_global
    if login_var == True:
        data = []
        print("\nCalculo de la media en la base de datos local:")
        for i in range(I_WRITE):
            data.append(elastic_client.get(index=tabla,id=i)['_source']['numero'])
            print('Elemento '+str(i)+' : '+str(data))

        def media(sum_values,num_values):
            return sum_values/num_values
            
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
        print('Acumulacion: '+str(sum_values))
        print('Nº de valores: '+str(num_values)+"\n")

        medialocal_global = str(mean)
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], 
                                mean_local=medialocal_global,mean_beebotte=mediainternet_global, user=user)
    else:
        medialocal_global = "No se puede obtener este valor sin estar registrado"
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], 
                                mean_local=medialocal_global,mean_beebotte=mediainternet_global, user=user)

@app.route("/media_internet") 
def internet_mean():
    """
    Esta función realiza el cálculo de la media de la base de datos de internet y actualiza la página web sacando su valor, si el usuario está loggeado y, 
    si no lo está, entonces no saca nada.
    """
    global mediainternet_global
    if login_var == True:
        lectura = bclient.read('cer_bbddserver',recurso,limit=I_WRITE)
        for i in range(len(lectura)):
            value = lectura[i]['data']
            print('Elemento '+str(i)+' : '+str(value))
        #print(str(lectura))

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
        print('Acumulacion: '+str(sum_values))
        print('Nº de valores: '+str(num_values)+"\n")

        mediainternet_global = str(mean)
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], mean_local=medialocal_global,
                                mean_beebotte=mediainternet_global, user=user)
    else:
        mediainternet_global = "No se puede obtener este valor sin estar registrado"
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], mean_local=medialocal_global,
                                mean_beebotte=mediainternet_global,user=user)

@app.route("/graficas") 
def graphs():
    if login_var == True:
        return redirect("https://beebotte.com/dash/a4986a00-38b9-11ec-954b-39d34f82886a?shareid=shareid_s410ZmUDNJAKMbfq") 
    else: 
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], mean_local=medialocal_global,
                                mean_beebotte=mediainternet_global,user=user)

def get_num_aleatorio():
    global I_WRITE
    while True: 
        r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
        elastic_client.index(index=tabla, id=I_WRITE, document={'numero':float(r)})
        bclient.write('cer_bbddserver',recurso,data=float(r))
        I_WRITE =I_WRITE+1
        time.sleep(120) #120

if __name__ == "__main__":

    hilo1 = Thread(target=get_num_aleatorio, daemon=True)
    hilo1.start()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    #app.run(host='0.0.0.0', port=5000, debug=True)