from flask import Flask, render_template 
import re, requests
app = Flask(__name__)

@app.route("/")
def num_aleatorio():
    return render_template('index.html')#re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]

if __name__ == "__main__":
    #app.run()
    app.run(host='0.0.0.0', port=5000, debug=True)