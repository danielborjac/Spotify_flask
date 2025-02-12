from datetime import datetime
import json 
import pymsgbox
import requests
import urllib.parse
from flask import Flask, jsonify, redirect, request, session
from json.decoder import JSONDecodeError


app= Flask(__name__)

app.secret_key = "53d355f8-571a-4590-a310-1f95794408512"

client_id = "ea25ac39ffef48f6b597669c764e599a"
client_secret = "552dc1dc29a7463a8d60f0007a40ec7d"
redirect_uri = "http://localhost:5000/callback"

auth_url = "https://accounts.spotify.com/authorize"
token_url = "https://accounts.spotify.com/api/token"
api_base_url = "https://api.spotify.com/v1/"

id_user = ""
username = ""
id_track = ""

@app.route("/")
def index():
    return ("<h1 style='text-align: center'> Prueba de conexión con Spotify</h1> "+
            "<div style='text-align: center; font-size: 20px'><br/><a href='/login'>Iniciar sesión<a></div>")


@app.route("/login")
def login():
    scope = 'user-read-private user-read-email user-follow-read user-library-read user-library-modify'
    
    param = {
        'client_id': client_id,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': redirect_uri,
        'show_dialog': False
    }
    
    url = f"{auth_url}?{urllib.parse.urlencode(param)}"
    
    return redirect(url)

@app.route("/callback")
def callback():
    if "error" in request.args:
        return jsonify({"error" : request.args['error']})

    if "code" in request.args:
        req_body = {
            "code": request.args["code"],
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        response = requests.post(token_url, data=req_body)
        token_info = response.json()
        
        session['access_token'] = token_info["access_token"]
        session['refresh_token'] = token_info["refresh_token"]
        session['expires_at'] = datetime.now().timestamp() + token_info["expires_in"]
        user_data()
        #return redirect("/playlists")
        #return redirect("/get_fav_artist")
        return redirect("/home")
    

@app.route("/refresh-token")
def refresh_token():
    if "refresh_token" not in session:
        return redirect("/login")
    
    if datetime.now().timestamp() > session["expires_at"]:
        req_body = {
            "grant_type": "refresh_token",
            "refresh_token": session["refresh_token"],
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        response = requests.post(token_url, data=req_body)
        new_token_info = response.json()
        
        session["access_token"] = new_token_info["access_token"]
        session['expires_at'] = datetime.now().timestamp() + new_token_info["expires_in"]
        user_data()
        #return redirect("/playlists")
        #return redirect("/get_fav_artist")
        return redirect("/home")
    
@app.route("/home")
def home():
     return ("<h1 style='text-align: center'>¡Login realizado con éxito!</h1>" + 
             "<div style='font-size: 20px; display: flex; justify-content: center;'><ul><li><a href='/playlists'>ver mis playlist</a></li>" +
             "<li><a href='/get_fav_artist'>ver mis artistas favoritos</a></li>"+
             "<li><a href='/get_saved_tracks'>ver mis canciones favoritas</a></li>"+
             "<li><a href='/send_id'>Guardar canción a favoritos</a></li>"+
             "<li><a href='/logout'>cerrar sesión</a></li></ul></div>")
    
    
def header_token():
       #token = 'BQDlHyQZ6QoBDyqF9l7-fj6atRG4rNchQDwYRQyovhbaKQZa2NE0WPyNXi4KMSmEaJ0eg3vIIVw3lJe2OXfkng0XvjH_8gN5TBcq4ATT4qEBSJFY17MMwP3iepEhgpCz7FPXUe21jU6uFfuJAtDdnDDpAzfG_2YE8YiWcnT1CNshNpFvT_MFfcfpf-M1Q2G7g5_YD2xMFR7GL0QO0PFlLsefYDiYMywW2KMRGaetsXnUSMYL-MfrsnHFuEL5li2MimLxGEXW2z1OxDGqtoxBQrZUbUaO5Z1h'
    if "access_token" not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect("/refresh-token")
    
    headers = {
        "Authorization": f"Bearer {session['access_token']}",
        "Content-Type": "application/json"
    }    
    print(headers)
    return headers
 
 
def user_data():  
    response = requests.get(api_base_url + "me/", headers=header_token())
    user = response.json()
    global id_user, username
    username = user["display_name"]
    id_user = user["id"]
    user_data = []
    
    with open('user.json', "rt") as fp:
        try:
            user_data = json.load(fp)
        except JSONDecodeError:
            pass
    
    result = [x for x in user_data if x["Spotify_id"]==id_user]
 
    if len(result)==0:
        query = {
            "id": len(user_data) + 1 ,
            "Spotify_id": user["id"],
            "User" : user["display_name"],
            "Email": user["email"],

        } 
        user_data.append(query)    
               
        with open('user.json', 'w') as file:
            json.dump(user_data,file,indent=4)
                   
    
@app.route("/playlists")
def get_playlist():  
    response = requests.get(api_base_url + "me/playlists", headers=header_token())
    playlists = response.json()
    
    user_playlists_info = [] 
    playlists_info = [(pl['name'], pl['external_urls']['spotify']) for pl in playlists['items']]   
     
    with open('playlist.json', "rt") as fp:
        try:
            user_playlists_info = json.load(fp)
        except JSONDecodeError:
            pass
        
    result = [x for x in user_playlists_info if x["User_id"]==id_user]
    query = {
        "id": len(user_playlists_info) + 1 ,
        "User_id": id_user,
        "User" : username,
        "Playlist": playlists_info
    }
    
    if len(result)==0:
        user_playlists_info.append(query)     
        
        with open('playlist.json', 'w') as file:
            json.dump(user_playlists_info,file,indent=4)
                   
    playlists_html = "<br>".join([f'{name}: {url}' for name, url in playlists_info]) + "<br/><br/><a href='/home'>Volver al inicio</a>"
       
    return playlists_html


@app.route("/get_fav_artist")
def get_artist():   
    response = requests.get(api_base_url + "me/following?type=artist", headers=header_token())
    artist = response.json()
    
    user_artists_info = [] 
    only_artist = artist['artists']
    artist_info = [(pl['name'], pl['external_urls']['spotify']) for pl in only_artist['items']]     
    
    with open('artist.json', "rt") as fp:
        try:
            user_artists_info = json.load(fp)
        except JSONDecodeError:
            pass
        
    result = [x for x in user_artists_info if x["User_id"]==id_user]
    query = {
        "id": len(user_artists_info) + 1 ,
        "User_id": id_user,
        "User" : username,
        "Artist": artist_info
    }
      
    if len(result)==0:
        user_artists_info.append(query)    
        with open('artist.json', 'w') as file:
            json.dump(user_artists_info ,file,indent=4) 
    
    artist_html = "<br>".join([f'{name}: {url}' for name, url in artist_info ]) + "<br/><br/><a href='/home'>Volver al inicio</a>"
    

    
    return artist_html


@app.route('/get_saved_tracks')
def get_saved_tracks(): 
    response = requests.get(api_base_url + "me/tracks", headers=header_token())
    tracks = response.json()   
    
    tracks_info = []     
    user_tracks_info = []
    for pl in tracks['items']:
        track = pl['track']
        try:
            tracks_info.append((track['name'], track['external_urls']['spotify']))
        except:
            pass
    
    with open('tracks.json', "rt") as fp:
        try:
            user_tracks_info = json.load(fp)
        except JSONDecodeError:
            pass
    
    result = [x for x in user_tracks_info if x["User_id"]==id_user]   
    
    query = {
        "id": len(user_tracks_info) + 1 ,
        "User_id": id_user,
        "User" : username,
        "Tracks": tracks_info
    } 
    
    tracks_html = "<br>".join([f'{name}: {url}' for name, url in tracks_info]) + "<br/><br/><a href='/home'>Volver al inicio</a>"
    
    if len(result)==0:
        user_tracks_info.append(query)    
        
        with open('tracks.json', 'w') as file:
            json.dump(user_tracks_info,file,indent=4)
    
    return tracks_html

   
@app.route('/send_id')
def send_id(): 
    global id_track
    id_track=pymsgbox.prompt('ingresa el id de la canción', default='')
    if id_track == None:
        return redirect('/home')
    else:
        return redirect('/save_track')

@app.route('/save_track')
def save_track(): 
    global id_track
    response = requests.put(api_base_url + "me/tracks?ids="+ id_track, headers=header_token())
    if response.status_code == 200:    
        track_html = "<h1>se ha guardado con éxito</h1><br/><br/><a href='/home'>Volver al inicio</a>"
        id_track = ""
    else:
        track_html = "<h1>hubo un error al tratar de guardar la canción</h1><br/><br/><a href='/home'>Volver al inicio</a>"
        id_track = ""
    return track_html



# log out
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True) 
    