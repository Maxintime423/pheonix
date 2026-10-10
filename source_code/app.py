from flask import Flask, redirect, render_template, send_from_directory, url_for
import os

server = Flask(__name__)


@server.route('/')
def index():
    return render_template('index.html')


@server.route('/download')
def download():
    return render_template('Download.html')


@server.route('/dld')
def dld():
    return redirect(url_for('download'))


@server.route('/manifest.json')
def manifest():
    return send_from_directory(os.path.join(server.root_path, 'p1'), 'manifest.json', mimetype='application/manifest+json')


@server.route('/service-worker.js')
@server.route('/sw.js')
def service_worker():
    response = send_from_directory(os.path.join(server.root_path, 'static'), 'sw.js', mimetype='application/javascript')
    return response


@server.route('/icons/<path:filename>')
def icons(filename):
    return send_from_directory(os.path.join(server.root_path, 'p1', 'icons'), filename)


if __name__ == "__main__":
    server.run(host='0.0.0.0', port=5000, debug=True)