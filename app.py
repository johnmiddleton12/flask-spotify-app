import os
from flask import Flask, session, jsonify, request, redirect, render_template
from flask_session import Session
import spotipy
import uuid

from flask_cors import CORS, cross_origin

import datetime
import time

import json

# socketio
# from flask_socketio import SocketIO, emit, send

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

# socketio
# socketio = SocketIO(app)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

def session_cache_path():
    return caches_folder + session.get('uuid')

def clear_listened(uid):
    with open(listen_folder + uid + '.json', 'w') as f:
        f.write(json.dumps({'songs': []}))

caches_folder2 = './.spotify_caches_temp/'
if not os.path.exists(caches_folder2):
    os.makedirs(caches_folder2)

def get_cache_path(user_id):
    return caches_folder2 + user_id

@app.route('/login', methods=['GET', 'POST'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
def login():

    # grab the token from the request
    request_data = request.get_json()
   
    token = json.loads(request_data['token'])
    # set expiring field for spotipy
    token['expires_at'] = int(request_data['expiresAt'])

    # make call to spotify to get user id for labeling cache
    spotify = spotipy.Spotify(auth=token['access_token'])
    uid = spotify.me()['id']

    # create cache handler to save the token
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=get_cache_path(uid))
    cache_handler.save_token_to_cache(token)

    return jsonify({
        'id': "YOU ARE: " + uid,
    })

@app.route('/')
def index():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-read-currently-playing playlist-modify-private',
            cache_handler=cache_handler, 
            show_dialog=True)

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # Step 4. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return f'<h2>Hi {spotify.me()["display_name"]}, ' \
            f'<small><a href="/sign_out">[sign out]<a/></small></h2>' \
            f'<a href="/playlists">my playlists</a> | ' \
            f'<a href="/currently_playing">currently playing</a> | ' \
            f'<a href="/current_user">me</a> | ' \
            f'<a href="/track">track songs</a>'


@app.route('/sign_out')
def sign_out():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')


@app.route('/playlists')
def playlists():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user_playlists()


@app.route('/currently_playing')
def currently_playing():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if not track is None:
        return track
    return "No track currently playing."


@app.route('/current_user')
def current_user():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user()

@app.route('/track', methods=['GET', 'POST'])
def track_songs():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)

    uid = spotify.me()['id']

    currently_tracking = uid in users_tracking

    if request.method == 'POST':
        if 'start tracking' in request.form:
            if not currently_tracking:
                print('starting process')
                users_tracking[uid] = spotify
            else:
                print('already tracking')

        elif 'stop tracking' in request.form:
            if currently_tracking:
                print('stopping')
                del users_tracking[uid]
            else:
                print('not tracking')

        elif 'clear songs' in request.form:
            print('clearing')
            clear_listened(uid)

    currently_tracking = uid in users_tracking

    try:
        with open(listen_folder + uid + '.json', 'r') as f:
            tracks = json.load(f)['songs']
    except:
        tracks = {'songs': []}

    return render_template('track.html', spotify=spotify, tracks=tracks, currently_tracking=currently_tracking)

if __name__ == '__main__':

    # socketio running
    # socketio.run(app, debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))