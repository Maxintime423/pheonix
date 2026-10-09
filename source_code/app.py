from flask import *

server = Flask(__name__)

@server.route('/')
def index():
    return render_template('index.html')

@server.route('/download')
def download():
    return send_from_directory(
        "p1/dwl" ,
        "econland.apk"
    )