from flask import Flask, render_template
import requests
import os

app = Flask(__name__)

# this is main app
# user will log in here
# login: they log in with spotify, then that refresh token is sent to the db

# user will be redirected to the main page

# user will be greeted with start, stop, and clear, and listened songs
# start: start process (container?) for the user
# stop: kill process (container?) for the user
# clear: clear db entry for the user

# the process:
#   every 2 seconds the currently listening song is logged to db

# TODO:
# 1. set up logging in (with spotify)
# 2. refresh token?

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
