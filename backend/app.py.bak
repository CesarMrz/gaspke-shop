import sqlite3
import json
import os
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
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            pin TEXT,
            expires TEXT,
            bought TEXT,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            total REAL,
            items INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    # Init balance if not exists
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('balance', '50.00')")
    # Seed platforms if empty
    c.execute("SELECT COUNT(*) as cnt FROM platforms")
    if c.fetchone()['cnt'] == 0:
        for p in DEFAULT_PLATFORMS:
            c.execute('''
                INSERT INTO platforms (id, name, icon, color, price, stock)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (p['id'], p['name'], p['icon'], p['color'], p['price'], p['stock']))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return send_from_directory('..', 'index.html')

@app.route('/api/platforms', methods=['GET'])
def get_platforms():
    conn = get_db()
    rows = conn.execute('SELECT * FROM platforms ORDER BY name').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/platforms', methods=['POST'])
def add_platform():
    data = request.json
    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO platforms (id, name, icon, color, price, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['id'], data['name'], data.get('icon', data['name'][0]), data.get('color', '#ff6b9d'), data['price'], data['stock']))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/platforms/<pid>', methods=['PUT'])
def update_platform(pid):
    data = request.json
    conn = get_db()
    conn.execute('''
        UPDATE platforms SET name=?, price=?, stock=?, color=?, icon=?
        WHERE id=?
    ''', (data.get('name'), data.get('price'), data.get('stock'), data.get('color'), data.get('icon'), pid))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route('/api/platforms/<pid>', methods=['DELETE'])
def delete_platform(pid):
    conn = get_db()
    conn.execute('DELETE FROM platforms WHERE id=?', (pid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route('/api/balance', methods=['GET'])
def get_balance():
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key='balance'").fetchone()
    conn.close()
    return jsonify({"balance": float(row['value']) if row else 50.0})

@app.route('/api/balance', methods=['POST'])
def update_balance():
    data = request.json
    amount = data.get('amount', 0)
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key='balance'").fetchone()
    current = float(row['value']) if row else 50.0
    new_bal = current + amount
    conn.execute("UPDATE settings SET value=? WHERE key='balance'", (str(new_bal),))
    conn.commit()
    conn.close()
    return jsonify({"balance": new_bal})

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    conn = get_db()
    rows = conn.execute('SELECT * FROM accounts ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.json
    items = data.get('items', [])  # [{id, name, price, months, qty}]
    if not items:
        return jsonify({"error": "Carrito vacío"}), 400

    total = sum(i['price'] * i['qty'] * i['months'] for i in items)
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key='balance'").fetchone()
    balance = float(row['value']) if row else 0
    if total > balance:
        conn.close()
        return jsonify({"error": "Saldo insuficiente"}), 400

    # Deduct balance
    new_bal = balance - total
    conn.execute("UPDATE settings SET value=? WHERE key='balance'", (str(new_bal),))

    # Create accounts & reduce stock
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
            exp = now + timedelta(days=30 * item['months'])
            email = f"user{os.urandom(2).hex()}@gaspke.shop"
            password = 'Pass' + os.urandom(4).hex() + '!'
            pin = str(1000 + (os.urandom(2)[0] % 9000))
            conn.execute('''
                INSERT INTO accounts (platform, email, password, pin, expires, bought, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (item['name'], email, password, pin, exp.strftime('%d/%m/%Y'), now.strftime('%d/%m/%Y'), now.isoformat()))
            created.append({"platform": item['name'], "email": email, "password": password, "pin": pin})

    conn.execute('INSERT INTO sales (date, total, items) VALUES (?, ?, ?)',
                 (now.isoformat(), total, sum(i['qty'] for i in items)))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "balance": new_bal, "accounts": created})

@app.route('/api/sales', methods=['GET'])
def get_sales():
    conn = get_db()
    rows = conn.execute('SELECT * FROM sales ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/reset', methods=['POST'])
def reset():
    # Optional: reset to defaults (for demo)
    conn = get_db()
    conn.execute('DELETE FROM accounts')
    conn.execute('DELETE FROM sales')
    conn.execute("UPDATE settings SET value='50.00' WHERE key='balance'")
    conn.execute('DELETE FROM platforms')
    for p in DEFAULT_PLATFORMS:
        conn.execute('''
            INSERT INTO platforms (id, name, icon, color, price, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (p['id'], p['name'], p['icon'], p['color'], p['price'], p['stock']))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

if __name__ == '__main__':
    init_db()
    print("Base de datos lista en:", DB_PATH)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
