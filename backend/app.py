import sqlite3, os, hashlib, secrets, json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DB_PATH = os.path.join(os.path.dirname(__file__), 'gaspke.db')

DEFAULT_PLATFORMS = [
    {"id":"netflix","name":"Netflix","icon":"N","color":"#e50914","price":3.50,"stock":47},
    {"id":"disney","name":"Disney+","icon":"D","color":"#113ccf","price":2.80,"stock":32},
    {"id":"max","name":"Max / HBO","icon":"M","color":"#7b2cbf","price":2.50,"stock":28},
    {"id":"prime","name":"Amazon Prime","icon":"A","color":"#00a8e1","price":2.20,"stock":19},
    {"id":"spotify","name":"Spotify","icon":"S","color":"#1db954","price":1.80,"stock":61},
    {"id":"yt","name":"YouTube Premium","icon":"Y","color":"#ff0000","price":2.00,"stock":24},
    {"id":"paramount","name":"Paramount+","icon":"P","color":"#0064ff","price":1.90,"stock":15},
    {"id":"crunchy","name":"Crunchyroll","icon":"C","color":"#f47521","price":1.50,"stock":38},
    {"id":"apple","name":"Apple TV+","icon":"A","color":"#000000","price":2.10,"stock":12},
    {"id":"hulu","name":"Hulu","icon":"H","color":"#1ce783","price":2.40,"stock":18},
    {"id":"peacock","name":"Peacock","icon":"P","color":"#000000","price":1.70,"stock":22},
    {"id":"discovery","name":"Discovery+","icon":"D","color":"#0073e6","price":1.60,"stock":14},
    {"id":"star","name":"Star+","icon":"S","color":"#ffd100","price":2.30,"stock":27},
    {"id":"vix","name":"Vix","icon":"V","color":"#ff3b30","price":1.20,"stock":45},
    {"id":"magis","name":"Magis TV","icon":"M","color":"#ff6b00","price":1.40,"stock":33},
    {"id":"iptv","name":"IPTV Premium","icon":"I","color":"#8b5cf6","price":4.50,"stock":50},
    {"id":"canva","name":"Canva Pro","icon":"C","color":"#00c4cc","price":1.90,"stock":40},
    {"id":"chatgpt","name":"ChatGPT Plus","icon":"G","color":"#10a37f","price":5.00,"stock":25},
]

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def get_db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = get_db()
    c.execute('''CREATE TABLE IF NOT EXISTS platforms (id TEXT PRIMARY KEY, name TEXT, icon TEXT, color TEXT, price REAL, stock INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT, balance REAL DEFAULT 50, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, platform TEXT, email TEXT, password TEXT, pin TEXT, expires TEXT, bought TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, total REAL, items INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id INTEGER, created_at TEXT)''')
    if c.execute('SELECT COUNT(*) FROM platforms').fetchone()[0] == 0:
        for p in DEFAULT_PLATFORMS:
            c.execute('INSERT INTO platforms VALUES (?,?,?,?,?,?)', (p['id'],p['name'],p['icon'],p['color'],p['price'],p['stock']))
    c.commit(); c.close()

def uid_from_token(t):
    if not t: return None
    c = get_db()
    r = c.execute('SELECT user_id FROM sessions WHERE token=?', (t,)).fetchone()
    c.close()
    return r['user_id'] if r else None

HTML = open('/dev/stdin').read() if False else '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GaspKe Shop</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root { --pink:#ffb6d9; --accent:#ff6b9d; --bg:#fff5fb; --text:#5a4a6a; --card:#fff; --border:#f0d0e8; }
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:Nunito,system-ui,sans-serif; background:linear-gradient(135deg,#fff5fb,#f3e8ff); color:var(--text); min-height:100vh; }
.sidebar { position:fixed; left:0; top:0; bottom:0; width:240px; background:linear-gradient(180deg,#fff0f7,#f8f0ff); padding:20px 12px; border-right:1px solid var(--border); }
.logo { text-align:center; font-weight:800; font-size:20px; color:var(--accent); margin-bottom:20px; }
.nav { padding:10px 12px; border-radius:12px; cursor:pointer; margin:4px 0; font-weight:700; }
.nav:hover, .nav.active { background:white; color:var(--accent); }
.main { margin-left:240px; padding:24px; }
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
.card { background:white; border-radius:16px; padding:16px; margin:8px; box-shadow:0 4px 16px rgba(255,182,217,.2); display:inline-block; min-width:180px; }
.btn { background:var(--accent); color:white; border:none; padding:8px 16px; border-radius:20px; cursor:pointer; font-weight:700; }
.modal { position:fixed; inset:0; background:rgba(0,0,0,.5); display:flex; align-items:center; justify-content:center; z-index:999; }
.box { background:white; padding:28px; border-radius:18px; width:90%; max-width:380px; }
input { width:100%; padding:12px; margin:8px 0; border:1px solid #eee; border-radius:10px; }
.hidden { display:none !important; }
</style>
</head>
<body>
<div id="auth" class="modal">
  <div class="box">
    <h2 id="atitle">Iniciar sesión</h2>
    <input id="aname" class="hidden" placeholder="Nombre">
    <input id="aemail" type="email" placeholder="Correo">
    <input id="apass" type="password" placeholder="Contraseña">
    <button class="btn" style="width:100%;margin-top:8px" onclick="doAuth()">Continuar</button>
    <p style="text-align:center;margin-top:12px"><span id="aswitch" onclick="toggleAuth()" style="color:var(--accent);cursor:pointer;font-weight:700">¿No tienes cuenta? Regístrate</span></p>
    <p id="aerr" style="color:red;text-align:center;margin-top:8px"></p>
  </div>
</div>
<div id="app" class="hidden">
  <div class="sidebar">
    <div class="logo">GaspKe Shop</div>
    <div class="nav active" onclick="show('dash')">Dashboard</div>
    <div class="nav" onclick="show('store')">Tienda</div>
    <div class="nav" onclick="show('accounts')">Mis Cuentas</div>
    <div class="nav" onclick="logout()">Cerrar sesión</div>
  </div>
  <div class="main">
    <div class="header">
      <h1 id="greet">¡Hola!</h1>
      <div>Saldo: $<span id="bal">50.00</span></div>
    </div>
    <div id="content"></div>
  </div>
</div>
<script>
let mode='login', token=localStorage.getItem('t'), user=JSON.parse(localStorage.getItem('u')||'null');
function greet(){ const h=new Date().getHours(); return h<12?'Buenos días':h<19?'Buenas tardes':'Buenas noches'; }
function showApp(){
  document.getElementById('auth').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
  document.getElementById('greet').textContent = greet()+', '+(user?user.name:'')+' ✨';
  document.getElementById('bal').textContent = (user?.balance||50).toFixed(2);
  show('dash');
}
function toggleAuth(){
  mode = mode==='login'?'register':'login';
  document.getElementById('atitle').textContent = mode==='login'?'Iniciar sesión':'Crear cuenta';
  document.getElementById('aname').classList.toggle('hidden', mode==='login');
  document.getElementById('aswitch').textContent = mode==='login'?'¿No tienes cuenta? Regístrate':'¿Ya tienes cuenta? Inicia sesión';
}
async function doAuth(){
  const name=document.getElementById('aname').value.trim();
  const email=document.getElementById('aemail').value.trim();
  const password=document.getElementById('apass').value;
  const err=document.getElementById('aerr'); err.textContent='';
  if(mode==='register' && !name) return err.textContent='Nombre obligatorio';
  if(!email||!password) return err.textContent='Datos incompletos';
  const r = await fetch(mode==='register'?'/api/register':'/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(mode==='register'?{name,email,password}:{email,password})});
  const d = await r.json();
  if(!r.ok) return err.textContent=d.error||'Error';
  token=d.token; user=d.user;
  localStorage.setItem('t',token); localStorage.setItem('u',JSON.stringify(user));
  showApp();
}
function logout(){ localStorage.clear(); location.reload(); }
async function show(sec){
  document.querySelectorAll('.nav').forEach(n=>n.classList.remove('active'));
  const c=document.getElementById('content');
  if(sec==='dash'||sec==='store'){
    const r=await fetch('/api/platforms'); const p=await r.json();
    c.innerHTML = p.map(x=>`<div class="card"><b style="color:${x.color}">${x.icon}</b> ${x.name}<br>$${x.price} <small>(${x.stock} stock)</small><br><button class="btn" style="margin-top:8px" onclick="buy('${x.id}','${x.name}',${x.price})">Comprar</button></div>`).join('');
  } else if(sec==='accounts'){
    const r=await fetch('/api/accounts',{headers:{Authorization:'Bearer '+token}});
    const a=await r.json();
    c.innerHTML = a.length? a.map(x=>`<div class="card"><b>${x.platform}</b><br>${x.email}<br>${x.password}</div>`).join('') : '<p>No tienes cuentas aún</p>';
  }
}
async function buy(id,name,price){
  if(!confirm('¿Comprar '+name+' por $'+price+'?')) return;
  const r=await fetch('/api/checkout',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({items:[{id,name,price,qty:1,months:1}]})});
  const d=await r.json();
  if(!r.ok) return alert(d.error||'Error');
  user.balance=d.balance; localStorage.setItem('u',JSON.stringify(user));
  document.getElementById('bal').textContent=d.balance.toFixed(2);
  alert('¡Comprado! Revisa Mis Cuentas');
  show('accounts');
}
if(token && user) showApp();
</script>
</body></html>'''

@app.route('/')
def index():
    r = make_response(HTML)
    r.headers['Cache-Control'] = 'no-store'
    return r

@app.route('/api/register', methods=['POST'])
def register():
    d = request.json
    name, email, pw = d.get('name','').strip(), d.get('email','').strip().lower(), d.get('password','')
    if not name or not email or not pw: return jsonify(error="Datos incompletos"), 400
    c = get_db()
    try:
        c.execute('INSERT INTO users (name,email,password,balance,created_at) VALUES (?,?,?,50,?)', (name,email,hash_pw(pw),datetime.now().isoformat()))
        c.commit()
        uid = c.execute('SELECT last_insert_rowid()').fetchone()[0]
        tok = secrets.token_hex(32)
        c.execute('INSERT INTO sessions VALUES (?,?,?)', (tok,uid,datetime.now().isoformat()))
        c.commit()
        u = c.execute('SELECT id,name,email,balance FROM users WHERE id=?',(uid,)).fetchone()
        c.close()
        return jsonify(ok=True, token=tok, user=dict(u))
    except Exception as e:
        c.close()
        return jsonify(error="Correo ya registrado" if "UNIQUE" in str(e) else str(e)), 400

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    email, pw = d.get('email','').strip().lower(), d.get('password','')
    c = get_db()
    u = c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
    if not u or u['password'] != hash_pw(pw):
        c.close(); return jsonify(error="Datos incorrectos"), 401
    tok = secrets.token_hex(32)
    c.execute('INSERT INTO sessions VALUES (?,?,?)', (tok,u['id'],datetime.now().isoformat()))
    c.commit(); c.close()
    return jsonify(ok=True, token=tok, user={"id":u['id'],"name":u['name'],"email":u['email'],"balance":u['balance']})

@app.route('/api/platforms')
def platforms():
    c = get_db()
    rows = c.execute('SELECT * FROM platforms').fetchall()
    c.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/accounts')
def accounts():
    uid = uid_from_token(request.headers.get('Authorization','').replace('Bearer ',''))
    if not uid: return jsonify([])
    c = get_db()
    rows = c.execute('SELECT * FROM accounts WHERE user_id=? ORDER BY id DESC',(uid,)).fetchall()
    c.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/checkout', methods=['POST'])
def checkout():
    uid = uid_from_token(request.headers.get('Authorization','').replace('Bearer ',''))
    if not uid: return jsonify(error="No autenticado"), 401
    items = request.json.get('items',[])
    if not items: return jsonify(error="Vacío"), 400
    c = get_db()
    u = c.execute('SELECT balance FROM users WHERE id=?',(uid,)).fetchone()
    total = sum(i['price']*i.get('qty',1)*i.get('months',1) for i in items)
    if u['balance'] < total:
        c.close(); return jsonify(error="Saldo insuficiente"), 400
    newb = u['balance'] - total
    c.execute('UPDATE users SET balance=? WHERE id=?',(newb,uid))
    now = datetime.now()
    created = []
    for it in items:
        p = c.execute('SELECT * FROM platforms WHERE id=?',(it['id'],)).fetchone()
        if not p or p['stock'] < it.get('qty',1):
            c.rollback(); c.close(); return jsonify(error=f"Sin stock de {it['name']}"), 400
        c.execute('UPDATE platforms SET stock=stock-? WHERE id=?',(it.get('qty',1),it['id']))
        for _ in range(it.get('qty',1)):
            em = f"user{os.urandom(2).hex()}@gaspke.shop"
            pw = 'Pass'+os.urandom(3).hex()+'!'
            pin = str(1000 + os.urandom(1)[0]%9000)
            exp = (now + timedelta(days=30)).strftime('%d/%m/%Y')
            c.execute('INSERT INTO accounts (user_id,platform,email,password,pin,expires,bought,created_at) VALUES (?,?,?,?,?,?,?,?)',
                      (uid,it['name'],em,pw,pin,exp,now.strftime('%d/%m/%Y'),now.isoformat()))
            created.append({"platform":it['name'],"email":em,"password":pw,"pin":pin})
    c.execute('INSERT INTO sales (user_id,date,total,items) VALUES (?,?,?,?)',(uid,now.isoformat(),total,sum(i.get('qty',1) for i in items)))
    c.commit(); c.close()
    return jsonify(ok=True, balance=newb, accounts=created)

init_db()
if __name__ == '__main__':
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port)
