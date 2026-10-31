import sqlite3
import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'gaspke.db')

DEFAULT_PLATFORMS = [
    {"id": "netflix", "name": "Netflix", "icon": "N", "color": "#e50914", "price": 3.50, "stock": 47},
    {"id": "disney", "name": "Disney+", "icon": "D", "color": "#113ccf", "price": 2.80, "stock": 32},
    {"id": "max", "name": "Max / HBO", "icon": "M", "color": "#7b2cbf", "price": 2.50, "stock": 28},
    {"id": "prime", "name": "Amazon Prime", "icon": "A", "color": "#00a8e1", "price": 2.20, "stock": 19},
    {"id": "spotify", "name": "Spotify", "icon": "S", "color": "#1db954", "price": 1.80, "stock": 61},
    {"id": "yt", "name": "YouTube Premium", "icon": "Y", "color": "#ff0000", "price": 2.00, "stock": 24},
]

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS platforms (id TEXT PRIMARY KEY, name TEXT, icon TEXT, color TEXT, price REAL, stock INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT, balance REAL DEFAULT 50.0, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, platform TEXT, email TEXT, password TEXT, pin TEXT, expires TEXT, bought TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, total REAL, items INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id INTEGER, created_at TEXT)''')
    if c.execute('SELECT COUNT(*) FROM platforms').fetchone()[0] == 0:
        for p in DEFAULT_PLATFORMS:
            c.execute('INSERT INTO platforms VALUES (?,?,?,?,?,?)', (p['id'], p['name'], p['icon'], p['color'], p['price'], p['stock']))
    conn.commit()
    conn.close()

def get_user_from_token(token):
    if not token: return None
    conn = get_db()
    row = conn.execute('SELECT user_id FROM sessions WHERE token=?', (token,)).fetchone()
    conn.close()
    return row['user_id'] if row else None

HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GaspKe Shop</title>
<style>
body { font-family: system-ui, sans-serif; background: #fff5fb; margin: 0; padding: 20px; }
.modal { position: fixed; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; }
.box { background: white; padding: 28px; border-radius: 16px; width: 90%; max-width: 380px; }
input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
button { width: 100%; padding: 12px; background: #ff6b9d; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }
.hidden { display: none; }
</style>
</head>
<body>
<div id="auth" class="modal">
  <div class="box">
    <h2 id="title">Iniciar sesión</h2>
    <input id="name" class="hidden" placeholder="Nombre">
    <input id="email" type="email" placeholder="Correo">
    <input id="pass" type="password" placeholder="Contraseña">
    <button onclick="doAuth()">Continuar</button>
    <p style="text-align:center; margin-top:12px;"><span onclick="toggle()" style="color:#ff6b9d; cursor:pointer; font-weight:bold;" id="switch">¿No tienes cuenta? Regístrate</span></p>
    <p id="error" style="color:red; text-align:center;"></p>
  </div>
</div>
<div id="app" class="hidden">
  <h1 id="greeting">¡Hola!</h1>
  <p>Saldo: $<span id="balance">50.00</span></p>
  <button onclick="logout()">Cerrar sesión</button>
  <div id="platforms"></div>
</div>
<script>
let mode = 'login';
let token = localStorage.getItem('token');
let user = JSON.parse(localStorage.getItem('user') || 'null');
function greeting() {
  const h = new Date().getHours();
  return h < 12 ? 'Buenos días' : h < 19 ? 'Buenas tardes' : 'Buenas noches';
}
function showApp() {
  document.getElementById('auth').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
  document.getElementById('greeting').textContent = greeting() + ', ' + (user ? user.name : '') + ' ✨';
  document.getElementById('balance').textContent = (user && user.balance || 50).toFixed(2);
  loadPlatforms();
}
function toggle() {
  mode = mode === 'login' ? 'register' : 'login';
  document.getElementById('title').textContent = mode === 'login' ? 'Iniciar sesión' : 'Crear cuenta';
  document.getElementById('name').classList.toggle('hidden', mode === 'login');
  document.getElementById('switch').textContent = mode === 'login' ? '¿No tienes cuenta? Regístrate' : '¿Ya tienes cuenta? Inicia sesión';
}
async function doAuth() {
  const name = document.getElementById('name').value.trim();
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('pass').value;
  const err = document.getElementById('error');
  err.textContent = '';
  if (mode === 'register' && !name) return err.textContent = 'Nombre obligatorio';
  if (!email || !password) return err.textContent = 'Correo y contraseña obligatorios';
  const res = await fetch(mode === 'register' ? '/api/register' : '/api/login', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify(mode === 'register' ? {name,email,password} : {email,password})
  });
  const data = await res.json();
  if (!res.ok) return err.textContent = data.error || 'Error';
  token = data.token; user = data.user;
  localStorage.setItem('token', token);
  localStorage.setItem('user', JSON.stringify(user));
  showApp();
}
function logout() {
  localStorage.clear(); token = null; user = null;
  document.getElementById('app').classList.add('hidden');
  document.getElementById('auth').classList.remove('hidden');
}
async function loadPlatforms() {
  const res = await fetch('/api/platforms');
  const plats = await res.json();
  document.getElementById('platforms').innerHTML = plats.map(p => 
    `<div style="margin:10px 0; padding:10px; background:white; border-radius:8px;">${p.name} - $${p.price}</div>`
  ).join('');
}
if (token && user) showApp();
</script>
</body>
</html>'''

@app.route('/')
def index():
    resp = make_response(HTML)
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name','').strip()
    email = data.get('email','').strip().lower()
    password = data.get('password','')
    if not name or not email or not password:
        return jsonify({"error": "Datos incompletos"}), 400
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (name,email,password,balance,created_at) VALUES (?,?,?,50,?)',
                     (name, email, hash_password(password), datetime.now().isoformat()))
        conn.commit()
        uid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        token = secrets.token_hex(32)
        conn.execute('INSERT INTO sessions VALUES (?,?,?)', (token, uid, datetime.now().isoformat()))
        conn.commit()
        user = conn.execute('SELECT id,name,email,balance FROM users WHERE id=?', (uid,)).fetchone()
        conn.close()
        return jsonify({"ok": True, "token": token, "user": dict(user)})
    except:
        conn.close()
        return jsonify({"error": "Correo ya registrado"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email','').strip().lower()
    password = data.get('password','')
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    if not user or user['password'] != hash_password(password):
        conn.close()
        return jsonify({"error": "Datos incorrectos"}), 401
    token = secrets.token_hex(32)
    conn.execute('INSERT INTO sessions VALUES (?,?,?)', (token, user['id'], datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "token": token, "user": {"id": user['id'], "name": user['name'], "email": user['email'], "balance": user['balance']}})

@app.route('/api/platforms')
def platforms():
    conn = get_db()
    rows = conn.execute('SELECT * FROM platforms').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
