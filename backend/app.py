import sqlite3
import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='..', static_url_path='')
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'gaspke.db')

DEFAULT_PLATFORMS = [
    {"id": "netflix", "name": "Netflix", "icon": "N", "color": "#e50914", "price": 3.50, "stock": 47},
    {"id": "disney", "name": "Disney+", "icon": "D", "color": "#113ccf", "price": 2.80, "stock": 32},
    {"id": "max", "name": "Max / HBO", "icon": "M", "color": "#7b2cbf", "price": 2.50, "stock": 28},
    {"id": "prime", "name": "Amazon Prime", "icon": "A", "color": "#00a8e1", "price": 2.20, "stock": 19},
    {"id": "spotify", "name": "Spotify", "icon": "S", "color": "#1db954", "price": 1.80, "stock": 61},
    {"id": "yt", "name": "YouTube Premium", "icon": "Y", "color": "#ff0000", "price": 2.00, "stock": 24},
    {"id": "paramount", "name": "Paramount+", "icon": "P", "color": "#0064ff", "price": 1.90, "stock": 15},
    {"id": "crunchy", "name": "Crunchyroll", "icon": "C", "color": "#f47521", "price": 1.50, "stock": 38},
    {"id": "apple", "name": "Apple TV+", "icon": "A", "color": "#000000", "price": 2.10, "stock": 12},
    {"id": "hulu", "name": "Hulu", "icon": "H", "color": "#1ce783", "price": 2.40, "stock": 18},
    {"id": "peacock", "name": "Peacock", "icon": "P", "color": "#000000", "price": 1.70, "stock": 22},
    {"id": "discovery", "name": "Discovery+", "icon": "D", "color": "#0073e6", "price": 1.60, "stock": 14},
    {"id": "star", "name": "Star+", "icon": "S", "color": "#ffd100", "price": 2.30, "stock": 27},
    {"id": "vix", "name": "Vix", "icon": "V", "color": "#ff3b30", "price": 1.20, "stock": 45},
    {"id": "magis", "name": "Magis TV", "icon": "M", "color": "#ff6b00", "price": 1.40, "stock": 33},
    {"id": "iptv", "name": "IPTV Premium", "icon": "I", "color": "#8b5cf6", "price": 4.50, "stock": 50},
    {"id": "canva", "name": "Canva Pro", "icon": "C", "color": "#00c4cc", "price": 1.90, "stock": 40},
    {"id": "chatgpt", "name": "ChatGPT Plus", "icon": "G", "color": "#10a37f", "price": 5.00, "stock": 25},
    {"id": "capcut", "name": "CapCut Pro", "icon": "C", "color": "#000000", "price": 1.50, "stock": 30},
    {"id": "deezer", "name": "Deezer", "icon": "D", "color": "#ff0090", "price": 1.60, "stock": 20},
    {"id": "tidal", "name": "Tidal", "icon": "T", "color": "#000000", "price": 2.20, "stock": 16},
    {"id": "dazn", "name": "DAZN", "icon": "D", "color": "#ffd200", "price": 3.80, "stock": 12},
    {"id": "espn", "name": "ESPN+", "icon": "E", "color": "#cc0000", "price": 2.90, "stock": 18},
    {"id": "mubi", "name": "MUBI", "icon": "M", "color": "#000000", "price": 2.50, "stock": 10},
    {"id": "crunchy_premium", "name": "Crunchyroll Mega Fan", "icon": "C", "color": "#f47521", "price": 2.80, "stock": 15},
    {"id": "hbo_max", "name": "Max Platino", "icon": "M", "color": "#7b2cbf", "price": 3.20, "stock": 20},
    {"id": "netflix_4k", "name": "Netflix 4K", "icon": "N", "color": "#e50914", "price": 4.50, "stock": 35},
    {"id": "disney_premium", "name": "Disney+ Premium", "icon": "D", "color": "#113ccf", "price": 3.50, "stock": 28},
    {"id": "prime_video", "name": "Prime Video", "icon": "P", "color": "#00a8e1", "price": 2.00, "stock": 22},
    {"id": "youtube_music", "name": "YouTube Music", "icon": "Y", "color": "#ff0000", "price": 1.70, "stock": 19},
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS platforms (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT,
            color TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL DEFAULT 50.0,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            platform TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            pin TEXT,
            expires TEXT,
            bought TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            total REAL,
            items INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # Init platforms if empty
    count = c.execute('SELECT COUNT(*) FROM platforms').fetchone()[0]
    if count == 0:
        for p in DEFAULT_PLATFORMS:
            c.execute('''
                INSERT INTO platforms (id, name, icon, color, price, stock)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (p['id'], p['name'], p['icon'], p['color'], p['price'], p['stock']))
    conn.commit()
    conn.close()

def get_user_from_token(token):
    if not token:
        return None
    conn = get_db()
    row = conn.execute('SELECT user_id FROM sessions WHERE token=?', (token,)).fetchone()
    conn.close()
    return row['user_id'] if row else None


@app.route('/version')
def version():
    return "GaspKe v2 - with auth"

@app.route('/')
def index():
    from flask import make_response
    import os
    html_path = os.path.join(os.path.dirname(__file__), '..', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    resp = make_response(html)
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not name or not email or not password:
        return jsonify({"error": "Nombre, correo y contraseña son obligatorios"}), 400
    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO users (name, email, password, balance, created_at)
            VALUES (?, ?, ?, 50.0, ?)
        ''', (name, email, hash_password(password), datetime.now().isoformat()))
        conn.commit()
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        token = secrets.token_hex(32)
        conn.execute('INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)',
                     (token, user_id, datetime.now().isoformat()))
        conn.commit()
        user = conn.execute('SELECT id, name, email, balance FROM users WHERE id=?', (user_id,)).fetchone()
        conn.close()
        return jsonify({"ok": True, "token": token, "user": dict(user)})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "El correo ya está registrado"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    if not user or user['password'] != hash_password(password):
        conn.close()
        return jsonify({"error": "Correo o contraseña incorrectos"}), 401
    token = secrets.token_hex(32)
    conn.execute('INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)',
                 (token, user['id'], datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "token": token, "user": {"id": user['id'], "name": user['name'], "email": user['email'], "balance": user['balance']}})

@app.route('/api/me', methods=['GET'])
def me():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = get_user_from_token(token)
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401
    conn = get_db()
    user = conn.execute('SELECT id, name, email, balance FROM users WHERE id=?', (user_id,)).fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(dict(user))

@app.route('/api/platforms', methods=['GET'])
def get_platforms():
    conn = get_db()
    rows = conn.execute('SELECT * FROM platforms').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = get_user_from_token(token)
    if not user_id:
        return jsonify([])
    conn = get_db()
    rows = conn.execute('SELECT * FROM accounts WHERE user_id=? ORDER BY id DESC', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/checkout', methods=['POST'])
def checkout():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = get_user_from_token(token)
    if not user_id:
        return jsonify({"error": "Debes iniciar sesión para comprar"}), 401
    data = request.json
    items = data.get('items', [])
    if not items:
        return jsonify({"error": "Carrito vacío"}), 400
    conn = get_db()
    user = conn.execute('SELECT balance FROM users WHERE id=?', (user_id,)).fetchone()
    total = sum(i['price'] * i['qty'] * i.get('months', 1) for i in items)
    if user['balance'] < total:
        conn.close()
        return jsonify({"error": "Saldo insuficiente"}), 400
    new_bal = user['balance'] - total
    conn.execute('UPDATE users SET balance=? WHERE id=?', (new_bal, user_id))
    now = datetime.now()
    created = []
    for item in items:
        plat = conn.execute('SELECT * FROM platforms WHERE id=?', (item['id'],)).fetchone()
        if not plat or plat['stock'] < item['qty']:
            conn.rollback()
            conn.close()
            return jsonify({"error": f"Stock insuficiente para {item['name']}"}), 400
        conn.execute('UPDATE platforms SET stock = stock - ? WHERE id=?', (item['qty'], item['id']))
        for _ in range(item['qty']):
            exp = now + timedelta(days=30 * item.get('months', 1))
            email = f"user{os.urandom(2).hex()}@gaspke.shop"
            password = 'Pass' + os.urandom(4).hex() + '!'
            pin = str(1000 + (os.urandom(2)[0] % 9000))
            conn.execute('''
                INSERT INTO accounts (user_id, platform, email, password, pin, expires, bought, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, item['name'], email, password, pin, exp.strftime('%d/%m/%Y'), now.strftime('%d/%m/%Y'), now.isoformat()))
            created.append({"platform": item['name'], "email": email, "password": password, "pin": pin})
    conn.execute('INSERT INTO sales (user_id, date, total, items) VALUES (?, ?, ?, ?)',
                 (user_id, now.isoformat(), total, sum(i['qty'] for i in items)))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "balance": new_bal, "accounts": created})

@app.route('/api/sales', methods=['GET'])
def get_sales():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = get_user_from_token(token)
    if not user_id:
        return jsonify([])
    conn = get_db()
    rows = conn.execute('SELECT * FROM sales WHERE user_id=? ORDER BY id DESC', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    init_db()
    print("Base de datos lista en:", DB_PATH)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
