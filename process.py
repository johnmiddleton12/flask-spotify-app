import os
import spotipy
import time
import json

from datetime import datetime

listen_folder = './.spotify_listen/'

if not os.path.exists(listen_folder):
    os.makedirs(listen_folder)

# separation of processes - currently using screen to run app &
# this func simultaneously - what is best approach?

# TODO: currently just tracks all the users in the spotify cache,
#       but should track the users that have opted in

# ideas: store in memory - redis?
# read list from there, maybe its map from user id to auth token?

def track_playing_songs(auth_manager):

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

if __name__ == '__main__':

    directory = './.spotify_caches_temp/'

    if not os.path.exists(directory):
        os.makedirs(directory)

    auth_managers = {
            # 'user_id': auth_manger object
    }

    # instantiate the auth managers
    for filename in os.listdir(directory):
        cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=directory + filename)
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
        auth_managers[filename] = auth_manager


    # print the current time as 12 hour time
    print(datetime.now().strftime('%I:%M%p'))

    while(1):
        for filename in os.listdir(directory):

            f = os.path.join(directory, filename)

            if filename not in auth_managers:
                cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=directory + filename)
                auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
                auth_managers[filename] = auth_manager
            
            track_playing_songs(auth_managers[filename])
    
        time.sleep(3)