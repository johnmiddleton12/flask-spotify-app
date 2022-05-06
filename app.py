import os
from flask import Flask, session, request, redirect, render_template
from flask_session import Session
from flask_socketio import SocketIO, send, emit
import spotipy
import uuid

import multiprocessing
import time

import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)
socketio = SocketIO(app)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

listen_folder = './.spotify_listen/'
if not os.path.exists(listen_folder):
    os.makedirs(listen_folder)

def session_cache_path():
    return caches_folder + session.get('uuid')

def clear_listened(uid):
    with open(listen_folder + uid + '.json', 'w') as f:
        f.write(json.dumps({'songs': []}))

processes = {}
def track_currently_playing(auth_manager):
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    uid = spotify.me()['id']

    try:
        with open(listen_folder + uid + '.json', 'r') as f:
            tracks = json.load(f)
    except FileNotFoundError:
        tracks = {
                'songs': [],
                }
        with open(listen_folder + uid + '.json', 'w') as f:
            f.write('')
    except:
        tracks = {
                'songs': [],
                }

    while True:
        try:
            current_track = spotify.current_user_playing_track()
            if current_track is not None:

                with open(listen_folder + uid + '.json', 'r') as f:
                    tracks = json.load(f)

                track_name = current_track['item']['name']

                song = {
                        'name': track_name,
                        'artist': current_track['item']['artists'][0]['name'],
                        'album': current_track['item']['album']['name'],
                        'url': current_track['item']['external_urls']['spotify'],
                        }

                if song not in tracks['songs']:
                    tracks['songs'].append(song)
                    with open(listen_folder + uid + '.json', 'w') as f:
                        f.write(json.dumps(tracks))

                    print(track_name + " added")

        except:
            pass
        finally:
            print('.', end='')
            time.sleep(1)


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

    # do stuff with token indefinitely, with another process

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    uid = spotify.me()['id']

    currently_tracking = uid in processes

    if request.method == 'POST':
        print(request.form)
        if 'start tracking' in request.form:
            if not uid in processes:
                print('starting process')
                processes[uid] = multiprocessing.Process(target=track_currently_playing, args=(auth_manager,))
                processes[uid].start()
            else:
                print('already tracking')
        elif 'stop tracking' in request.form:
            if uid in processes:
                print('stopping')
                processes.pop(uid).terminate()
            else:
                print('not tracking')
        elif 'clear songs' in request.form:
            print('clearing')
            clear_listened(uid)

    try:
        with open(listen_folder + uid + '.json', 'r') as f:
            tracks = json.load(f)['songs']
        print('loaded tracks')
    except:
        tracks = {'songs': []}

    return render_template('track.html', spotify=spotify, tracks=tracks, currently_tracking=currently_tracking)

@socketio.on('connect')
def connect():
    print('connected')

@socketio.on('my event')
def handle_my_custom_event(json_in):
    print('received interval event')
    uid = json_in['data']
    try:
        with open(listen_folder + uid + '.json', 'r') as f:
            tracks = json.load(f)
    except:
        tracks = {'songs': []}

    emit('my response', tracks, broadcast=True)

if __name__ == '__main__':
    # socketio.run(app, debug=True)
    # socketio.run(app, debug=True, threaded=True, port=int(os.environ.get("PORT", os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))
    socketio.run(app, debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))
