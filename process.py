import os
import spotipy
import time
import json

listen_folder = './.spotify_listen/'

# TODO: currently just tracks all the users in the spotify cache,
#       but should track the users that have opted in

def track_playing_songs(spotify):

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

    directory = './.spotify_caches/'

    people = {}

    while(1):
        for filename in os.listdir(directory):

            f = os.path.join(directory, filename)

            if filename not in people:
                cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=directory + filename)
                auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)

                people[filename] = spotipy.Spotify(auth_manager=auth_manager)
            
            track_playing_songs(people[filename])
    
        time.sleep(3)