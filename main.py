from datetime import datetime
import requests
import urllib.parse
from flask import Flask, jsonify, redirect, request, session

app= Flask(__name__)

app.secret_key = "53d355f8-571a-4590-a310-1f95794408512"

client_id = "ea25ac39ffef48f6b597669c764e599a"
client_secret = "552dc1dc29a7463a8d60f0007a40ec7d"
redirect_uri = "http://localhost:5000/callback"

auth_url = "https://accounts.spotify.com/authorize"
token_url = "https://accounts.spotify.com/api/token"
api_base_url = "https://api.spotify.com/v1/"

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
        return redirect("/home")

def header_token():
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

@app.route("/home")
def home():
     return ("<h1 style='text-align: center'>¡Login realizado con éxito!</h1>" + 
             "<div style='font-size: 20px; display: flex; justify-content: center;'><ul><li><a href='/playlists'>ver mis playlist</a></li>")

if __name__ == '__main__':
    app.run(debug=True) 

