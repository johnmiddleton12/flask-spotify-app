from flask import Flask, render_template

import requests

import os

app = Flask(__name__)

@app.route('/')
def hello_world():

    r = requests.get(os.environ.get('SPOTIFY_API_URL'))
    if r.json():
        fetched = r.json()['songs']
    else:
        fetched = []

    # open listened file
    return render_template('index.html', listened=fetched)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
