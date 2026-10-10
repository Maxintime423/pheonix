from flask import *

server = Flask(__name__)

@server.route('/')
def index():
    return render_template('index.html')


@server.route('/download')
def download():
    return render_template('download.html')
@server.route('/dld')
def dld():
    return redirect(url_for('download'))

if __name__ == "__main__":
    server.run()