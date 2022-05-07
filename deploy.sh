#git clone https://github.com/johnmiddleton12/flask-spotify-app.git

cp ../envvars.sh ./

#cd flask-spotify-app

python3 -m venv env
source env/bin/activate
source envvars.sh

pip3 install -r requirements.txt

python3 app.py
