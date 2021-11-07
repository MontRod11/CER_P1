from flask import Flask, render_template, redirect, request,session
from elasticsearch import Elasticsearch
import re, requests, uuid, hashlib, time
from flask.helpers import total_seconds
from threading import Thread
from beebotte import *

# Variables de escritura en las bases de datos
I_WRITE = 0
I_WRITE_NAMES = 0
# Variable que indica si hay sesión iniciada o no
login_var = False
# Variable global de usuario, media local y media global y numero de veces que se accede al resultado de la media.
user = "Iniciar Sesión"
medialocal_global = "No se puede obtener este valor sin estar registrado"
mediainternet_global = "No se puede obtener este valor sin estar registrado"
num_veces_elastic = 0
num_veces_beebotte =  0
# Variables de control
bad_pass = 0
ya_registrado = 0


# Creación del cliente de la base de datos local. Esta se aloja en el puerto 9200
elastic_client = Elasticsearch([{'host':'localhost','port':9200}])
# Creación del cliente de la base de datos de internet, usando un token y hostname en vez de la API Key y SECRET Key.
token = 'token_5YNOoMGF3pj5EP1f'
hostname = 'api.beebotte.com'
bclient = BBT(token=token,hostname=hostname)
recurso="bbddserver_2"

# Importación de la clase "Flask" y creación de la instancia, necesario para que Flask sepa donde buscar los recursos como "templates" y ficheros estáticos.
app = Flask(__name__)
app.secret_key = 'lausi'

# Creación de las tablas de la base de datos local en las que se van a guardar los números aleatorios, datos de usuario, y número de veces que se almacena la media.
tabla = "tabla2"
elastic_client.indices.create(index=tabla, ignore=400)
elastic_client.indices.delete(index=tabla, ignore=[400,404])
tabla_nombres = "tabla_nombres1"
tabla_num_medias = "tabla_medias"
elastic_client.indices.create(index=tabla_nombres, ignore=400)
elastic_client.indices.create(index=tabla_num_medias, ignore=400)

@app.route("/") # El uso de route() dice a Flask en que URL se debe ejecutar la función.
def inicio():
    """
    Esta función es la funcion base e inicial del programa, en este caso solo se actualiza el indice sacando un número aleatorio de la pagina web numero al azar
    """
    r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
    return render_template('index.html',num_aleat=r, mean_local = medialocal_global, mean_beebotte=mediainternet_global, user=user, num_veces_elastic=num_veces_elastic,num_veces_beebotte=num_veces_beebotte)

@app.route("/umbral1",methods = ["POST"])
def umbral1():
    """
    Esta función es la funcion que permite mostral el umbral histórico que supera cierto umbral:
    - Si no se ha introducido un número entonces devuelve una página que indica error.
    - Si la base de datos está vacía entonces indica un '0'.
    - Si solo hay 5 números en la base de datos solo muestra aquellos que superan el umbral.
    - Si hay más de 5 números en la base de datos, muestra los últimos 5 que superan el umbrales.
    """
    umbral=request.form['umbral']
    if umbral == '':
        return render_template('umbral1_noumbral.html')
    else:
        umbral = int(umbral)
    if I_WRITE == 0:
        hist = 0
        return render_template('umbral1.html', historico=str(hist), umbral=umbral)
    elif I_WRITE < 5:
        hist = []
        for i in range(I_WRITE):
            aux = elastic_client.get(index=tabla,id=i)['_source']['numero']
            if aux > umbral:
                hist.append(aux)
        return render_template('umbral1.html',historico=str(hist), umbral=umbral)       
    else:
        hist = []
        j = 0
        for i in range(I_WRITE,0,-1):
            aux = elastic_client.get(index=tabla,id=i-1)['_source']['numero']
            if aux > umbral:
                hist.append(aux)
                j = j +1
            if j == 5:
                break   
        return render_template('umbral1.html', historico=str(hist), umbral=umbral)

@app.route("/hello")
def hello():
    """ 
    Esta funcion es una función de prueba que permite ver en la terminal las bases de datos y sus contenidos y muestra en la página el último elemento que se
    ha incluido en la base de datos local, y de internet.
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
    return render_template('/laura/index.html',num_aleat=str(data), mean_local = medialocal_global, mean_beebotte=mediainternet_global, user=user,
                            num_veces_elastic=num_veces_elastic,num_veces_beebotte=num_veces_beebotte)

@app.route("/login")
def login():
    """Realizar el login"""
    return render_template("indexlogin.html")  

@app.route("/loggeado",methods = ["POST"])
def loggeado():
    """
    En esta función se realiza el login como tal:
    - Si no se ha introducido usuario entonces se devuelve una página web en la que se indica que se debe introducir un nombre de usuario correcto.
    - Si el usuario ya esta con la sesión iniciada se devuelve una página en la que se indica que el usuario ya está loggeado.
    - Si la base de datos de usuario está vacía se indica que el usuario debe registrarse previamente.
    - Si hay usuarios registrados en la base de datos entonces se comprueba si el usuario está registrado:
            · Si el usuario está registrado se comprueba la contraseña (si la contraseña cifrada coincide con la almacenada en la base de datos entonces
            se inicia sesión, si la contraseña no coincide entonces se indica al usuario que la contraseña introducida es incorrecta)
            · Si el usuario no está registrado se le indica que se registre previamente. 
    """
    global I_WRITE_NAMES
    global login_var
    global user
    global bad_pass
    global num_veces_beebotte
    global num_veces_elastic
    global indice_usuario
    if bad_pass == 1:
       user_prev = '0'
    else:
       user_prev = user
    #user_prev = user
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
                    salt = elastic_client.get(index=tabla_nombres,id=i)['_source']['sal']
                    # Codificamos la password con la salt para ver si salen igual
                    passw =  hashlib.sha512(password.encode('utf-8') + salt.encode('utf-8')).hexdigest()
                    print('Nombre '+str(i)+' : '+nombre)
                    if (nombre == user) and (passw == passkey):
                        session['username'] = user
                        """ Inicio de sesión:
                            - Comprobar contraseña
                            - Devolver el index con la sesión iniciada
                        """
                        indice_usuario = i
                        num_veces_beebotte =  elastic_client.get(index=tabla_num_medias,id=i)['_source']['num_beebotte']
                        num_veces_elastic =  elastic_client.get(index=tabla_num_medias,id=i)['_source']['num_elastic']
                        login_var = True
                        r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
                        return render_template('index.html',num_aleat=r, mean_local = medialocal_global, mean_beebotte=mediainternet_global, user=user,num_veces_elastic=num_veces_elastic,num_veces_beebotte=num_veces_beebotte)
                    elif (nombre == user) and (passw != passkey):
                        bad_pass = 1
                        return render_template('indexlogin badpass.html')
                return render_template('falloiniciosesionnosignin.html')        
                # else:
                #         """Devolver nuevo index donde se indique que no está loggeado"""
                #         return render_template('falloiniciosesionnosignin.html')

@app.route("/signin")  
def signin():
    """Realizar el signin metiendo el ususario en la base de datos y usandolo como inicio de sesion"""
    return render_template("indexsignin.html")  

@app.route("/registrado",methods = ["POST"])
def registrado():
    """
    En esta función se realiza el registro como tal:
    - Si no se ha introducido usuario entonces se devuelve una página web en la que se indica que se debe introducir un nombre de usuario correcto.
    - Si la base de datos de usuario está vacía se comienza el proceso de cifrado de la contraseña y se almancena usuario, sal y contraseña cifrada en la base de datos de 
    nombres y se crea una base de datos donde se asocia a cada usuario una variable en la que se almacena el número de veces que pide la media (inicializado a cero).
    - Si hay usuarios registrados en la base de datos entonces se comprueba si el usuario está registrado:
            · Si el usuario está registrado entonces devuelve una página en la que indica al usuario que ya esta registrado y que puede iniciar sesión.
            · Si el usuario no está registrado entonces se comienza el proceso de cifrado de la contraseña y se almancena usuario, sal y contraseña cifrada en la base de datos de 
            nombres y se crea una base de datos donde se asocia a cada usuario una variable en la que se almacena el número de veces que pide la media (inicializado a cero).
    """
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
                passw =  hashlib.sha512(password.encode('utf-8') + salt.encode('utf-8')).hexdigest() #Fuente: https://www.iteramos.com/pregunta/44612/la-sal-y-el-hash-de-una-contrasena-en-python
                #passw =  hashlib.sha512(password + salt).hexdigest()
                elastic_client.index(index=tabla_nombres, id=I_WRITE_NAMES, document={'nombre':user_reg,'password':passw,'sal':salt})
                elastic_client.index(index=tabla_num_medias, id=I_WRITE_NAMES, document={'nombre':user_reg,'num_elastic':0,'num_beebotte':0})
                #elastic_client.index(index=tabla_nombres, id=I_WRITE_NAMES, document={'nombre':user_reg,'password':passw,'sal':salt,'num_elastic':0,'num_beebotte':0})
                #elastic_client.index(index=tabla_nombres, id=I_WRITE_NAMES, document={'nombre':user_reg,'password':passw,'sal':salt,'num_elastic':num_veces_elastic,'num_beebotte':num_veces_beebotte})
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
                    passw =  hashlib.sha512(password.encode('utf-8') + salt.encode('utf-8')).hexdigest()
                    elastic_client.index(index=tabla_nombres, id=I_WRITE_NAMES, document={'nombre':user_reg,'password':passw,'sal':salt})
                    elastic_client.index(index=tabla_num_medias, id=I_WRITE_NAMES, document={'nombre':user_reg,'num_elastic':0,'num_beebotte':0})
                    # elastic_client.index(index=tabla_nombres, id=I_WRITE_NAMES, document={'nombre':user_reg,'password':passw,'sal':salt,'num_elastic':0,'num_beebotte':0})
                    # elastic_client.index(index=tabla_nombres, id=I_WRITE_NAMES, document={'nombre':user_reg,'password':passw,'sal':salt,'num_elastic':num_veces_elastic,'num_beebotte':num_veces_beebotte})
                    I_WRITE_NAMES =I_WRITE_NAMES+1
                    return render_template('indexlogin.html')
    
@app.route("/logout") 
def logout():
    """
    Funcion en la que se realiza el logout, si no hay ningún usuario loggeado entonces devuelve un indice en el que se indica que debe iniciar sesión, y si hay usuario loggeado
    entonces guarda en la base de datos que almacena el número de veces que cada usuario pide la base de datos.
    Reinicia el resto de variables, cierra la sesuón e indica que no hay usuario loggeado.
    """
    global login_var
    global medialocal_global
    global mediainternet_global
    global user
    global num_veces_beebotte
    global num_veces_elastic
    if user == "Iniciar Sesión":
        # elastic_client.index(index=tabla_num_medias, id=indice_usuario, document={'nombre':user,'num_elastic':num_veces_elastic,'num_beebotte':num_veces_beebotte})
        num_veces_elastic = "Inicie sesion"
        num_veces_beebotte = "Inicie sesion"
        session.pop(user,None)
        user = "Iniciar Sesión"
        login_var = False
        mediainternet_global = "No se puede obtener este valor sin estar registrado"
        medialocal_global = "No se puede obtener este valor sin estar registrado"
        return render_template("indexlogout.html") 
    else:
        elastic_client.index(index=tabla_num_medias, id=indice_usuario, document={'nombre':user,'num_elastic':num_veces_elastic,'num_beebotte':num_veces_beebotte})
        num_veces_elastic = "Inicie sesion"
        num_veces_beebotte = "Inicie sesion"
        session.pop(user,None)
        user = "Iniciar Sesión"
        login_var = False
        mediainternet_global = "No se puede obtener este valor sin estar registrado"
        medialocal_global = "No se puede obtener este valor sin estar registrado"
        return render_template("indexlogout.html") 

@app.route("/media_local") 
def local_mean():
    """
    Esta función realiza el cálculo de la media de la base de datos local y actualiza la página web sacando su valor, si el usuario está loggeado, y, si no lo 
    está, entonces no saca nada.
    """
    global medialocal_global
    global num_veces_elastic
    if login_var == True:
        data = []
        print("\nCalculo de la media en la base de datos local:")
        for i in range(I_WRITE):
            # saca todos los números que hay en la base de datos
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

        # calculo de la media
        sum_values, num_values = get_values(data)
        mean = media(sum_values,num_values)

        print('La media es:'+str(mean))
        print('Acumulacion: '+str(sum_values))
        print('Nº de valores: '+str(num_values)+"\n")
        # aumenta el número de veces que se ha pedido la media local
        num_veces_elastic =  str(int(num_veces_elastic) +1)
        medialocal_global = str(mean)
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], 
                                mean_local=medialocal_global,mean_beebotte=mediainternet_global, user=user,num_veces_elastic=num_veces_elastic,num_veces_beebotte=num_veces_beebotte)
    else:
        medialocal_global = "No se puede obtener este valor sin estar registrado"
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], 
                                mean_local=medialocal_global,mean_beebotte=mediainternet_global, user=user,num_veces_elastic=num_veces_elastic,num_veces_beebotte=num_veces_beebotte)

@app.route("/media_internet") 
def internet_mean():
    """
    Esta función realiza el cálculo de la media de la base de datos de internet y actualiza la página web sacando su valor, si el usuario está loggeado, y, 
    si no lo está, entonces no saca nada.
    """
    global num_veces_beebotte
    global mediainternet_global
    if login_var == True:
        # saca todos los números que hay en la base de datos
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

        # calculo de la media
        sum_values, num_values = get_values(lectura)
        mean = media(sum_values,num_values)

         # aumenta el número de veces que se ha pedido la media de internet
        print('La media es:'+str(mean))
        print('Acumulacion: '+str(sum_values))
        print('Nº de valores: '+str(num_values)+"\n")
        num_veces_beebotte = str(int(num_veces_beebotte) +1)
        mediainternet_global = str(mean)
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], mean_local=medialocal_global,
                                mean_beebotte=mediainternet_global, user=user,num_veces_elastic=num_veces_elastic,num_veces_beebotte=num_veces_beebotte)
    else:
        mediainternet_global = "No se puede obtener este valor sin estar registrado"
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], mean_local=medialocal_global,
                                mean_beebotte=mediainternet_global,user=user,num_veces_elastic=num_veces_elastic,num_veces_beebotte=num_veces_beebotte)

@app.route("/graficas") 
def graphs():
    """ Si hay usuario loggeado devuelve la gráfica asociada al recurso creado para la base de datos de internet, si no lo está entonces devuelve el propio índice """
    if login_var == True:
        return redirect("https://beebotte.com/dash/a4986a00-38b9-11ec-954b-39d34f82886a?shareid=shareid_s410ZmUDNJAKMbfq") 
    else: 
        return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4], mean_local=medialocal_global,
                                mean_beebotte=mediainternet_global,user=user,num_veces_elastic=num_veces_elastic,num_veces_beebotte=num_veces_beebotte)

def get_num_aleatorio():
    """ función que se ejecuta cada dos minutos gracias a un hilo donde se va almacenando un número aleatorio en las distintas bases de datos"""
    global I_WRITE
    while True: 
        r = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
        elastic_client.index(index=tabla, id=I_WRITE, document={'numero':float(r)})
        bclient.write('cer_bbddserver',recurso,data=float(r))
        I_WRITE =I_WRITE+1
        time.sleep(120) #120

if __name__ == "__main__":
    """ Función main, inicializa el hilo que va a introducir números en la base de datos cada dos minutos y inicializa la aplicación del servidor web en el puerto 5000 del localhost """
    hilo1 = Thread(target=get_num_aleatorio, daemon=True)
    hilo1.start()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
