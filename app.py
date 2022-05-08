import os
from flask import Flask, jsonify, request, redirect, render_template
import spotipy
import uuid

from flask_cors import CORS, cross_origin

import datetime
import time

import json

app = Flask(__name__)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

def get_cache_path(uid):
    return caches_folder + uid 

def get_listening_path(uid):
    return './.spotify_listen' + uid + '.json'

def clear_listened(uid):
    with open(listen_folder + uid + '.json', 'w') as f:
        f.write(json.dumps({'songs': []}))

@app.route('/starttrack', methods=['GET', 'POST'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
def starttrack():

    # grab the token from the request
    request_data = request.get_json()
   
    token = json.loads(request_data['token'])
    # set expiring field for spotipy
    token['expires_at'] = int(request_data['expiresAt'])

    # make call to spotify to get user id for labeling cache
    spotify = spotipy.Spotify(auth=token['access_token'])
    uid = spotify.me()['id']

    print("STARTING TRACKING FOR: " + uid)

    # create cache handler to save the token
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=get_cache_path(uid))
    cache_handler.save_token_to_cache(token)

    return jsonify({
        'id': "YOU ARE: " + uid,
    })

@app.route('/endtrack', methods=['GET', 'POST'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
def endtrack():

    request_data = request.get_json()
    token = json.loads(request_data['token'])

    spotify = spotipy.Spotify(auth=token['access_token'])
    uid = spotify.me()['id']

    print("STOPPING TRACKING FOR: " + uid)
    os.remove(get_cache_path(uid))

    return jsonify({
        'id': "YOU ARE: " + uid,
    })

@app.route('/getlistened', methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
def getlistened():

    request_data = request.get_json()
    token = json.loads(request_data['token'])

    spotify = spotipy.Spotify(auth=token['access_token'])
    uid = spotify.me()['id']

    print("GETTING LISTENED FOR: " + uid)

    with open(get_listening_path(uid), 'r') as f:
        tracks = json.load(f)

    return jsonify({
        'id': "YOU ARE: " + uid,
        'tracks': tracks['songs'],
    })

if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))