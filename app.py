import os
from flask import Flask, session, request, redirect, render_template
from flask_session import Session
import spotipy
import uuid

import datetime, threading

import time

import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

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

users_tracking = {
        # 'user_id': spotify object
}

# for every user that has enabled tracking, write their current track to a file
# only needs one extra thread
def track_playing_songs():

    global users_tracking

    for uid in users_tracking:

        spotify = users_tracking[uid]

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

        current_track = spotify.current_user_playing_track()
        if current_track is not None:

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

    threading.Timer(1, track_playing_songs).start()

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

    track_playing_songs()

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))
