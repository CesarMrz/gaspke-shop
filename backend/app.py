import sqlite3, os, hashlib, secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DB_PATH = os.path.join(os.path.dirname(__file__), 'gaspke.db')

DEFAULT_PLATFORMS = [
    {"id":"netflix","name":"Netflix","icon":"N","color":"#e50914","price":3.50,"stock":47},
    {"id":"disney","name":"Disney+","icon":"D","color":"#113ccf","price":2.80,"stock":32},
    {"id":"max","name":"Max","icon":"M","color":"#7b2cbf","price":2.50,"stock":28},
    {"id":"prime","name":"Prime Video","icon":"P","color":"#00a8e1","price":2.20,"stock":19},
    {"id":"spotify","name":"Spotify","icon":"S","color":"#1db954","price":1.80,"stock":61},
    {"id":"yt","name":"YouTube","icon":"Y","color":"#ff0000","price":2.00,"stock":24},
    {"id":"paramount","name":"Paramount+","icon":"P","color":"#0064ff","price":1.90,"stock":15},
    {"id":"crunchy","name":"Crunchyroll","icon":"C","color":"#f47521","price":1.50,"stock":38},
    {"id":"apple","name":"Apple TV+","icon":"A","color":"#000","price":2.10,"stock":12},
    {"id":"hulu","name":"Hulu","icon":"H","color":"#1ce783","price":2.40,"stock":18},
    {"id":"canva","name":"Canva Pro","icon":"C","color":"#00c4cc","price":1.90,"stock":40},
    {"id":"chatgpt","name":"ChatGPT Plus","icon":"G","color":"#10a37f","price":5.00,"stock":25},
    {"id":"capcut","name":"CapCut Pro","icon":"C","color":"#000","price":1.50,"stock":30},
    {"id":"iptv","name":"IPTV Premium","icon":"I","color":"#8b5cf6","price":4.50,"stock":50},
]

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def get_db():
    c = sqlite3.connect(DB_PATH); c.row_factory = sqlite3.Row; return c

def init_db():
    c = get_db()
    c.execute('CREATE TABLE IF NOT EXISTS platforms (id TEXT PRIMARY KEY, name TEXT, icon TEXT, color TEXT, price REAL, stock INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT, balance REAL DEFAULT 50, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, platform TEXT, email TEXT, password TEXT, pin TEXT, expires TEXT, bought TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, date TEXT, total REAL, items INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id INTEGER, created_at TEXT)')
    if c.execute('SELECT COUNT(*) FROM platforms').fetchone()[0] == 0:
        for p in DEFAULT_PLATFORMS:
            c.execute('INSERT INTO platforms VALUES (?,?,?,?,?,?)', (p['id'],p['name'],p['icon'],p['color'],p['price'],p['stock']))
    c.commit(); c.close()

def uid(t):
    if not t: return None
    c = get_db(); r = c.execute('SELECT user_id FROM sessions WHERE token=?',(t,)).fetchone(); c.close()
    return r['user_id'] if r else None

HTML = r'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GaspKe Shop</title>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--accent:#ff6b9d;--bg:#fff5fb;--text:#5a4a6a;--card:#ffffff;--border:#f0d0e8;--shadow:0 8px 30px rgba(255,182,217,.22)}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Nunito,system-ui,sans-serif;background:linear-gradient(135deg,#fff5fb 0%,#f3e8ff 50%,#ffe6f2 100%);color:var(--text);min-height:100vh}
.sidebar{position:fixed;left:0;top:0;bottom:0;width:260px;background:linear-gradient(180deg,#fff0f7,#f8f0ff);border-right:1px solid var(--border);padding:24px 16px;display:flex;flex-direction:column;box-shadow:4px 0 24px rgba(255,182,217,.12)}
.logo-box{text-align:center;margin-bottom:28px}
.logo-box img{width:120px;height:120px;border-radius:20px;object-fit:cover;box-shadow:var(--shadow);margin-bottom:8px}
.logo-text{font-weight:800;font-size:18px;color:var(--accent)}
.nav{display:flex;align-items:center;gap:10px;padding:12px 14px;border-radius:14px;cursor:pointer;margin-bottom:4px;font-weight:700;font-size:14.5px;color:#8a7a9a;transition:.2s}
.nav:hover,.nav.active{background:white;color:var(--accent);box-shadow:0 4px 14px rgba(255,107,157,.12)}
.main{margin-left:260px;padding:28px 32px}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}
.top h1{font-size:26px;font-weight:800}
.bal{background:white;padding:10px 18px;border-radius:30px;font-weight:800;box-shadow:var(--shadow);font-size:15px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:18px}
.card{background:white;border-radius:18px;padding:18px;box-shadow:var(--shadow);transition:.2s;text-align:center;border:1px solid transparent}
.card:hover{transform:translateY(-5px);border-color:var(--accent)}
.icon{width:48px;height:48px;border-radius:14px;display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:20px;margin:0 auto 12px}
.name{font-weight:800;font-size:15px;margin-bottom:4px}
.price{color:var(--accent);font-weight:800;font-size:18px;margin:6px 0}
.stock{font-size:12px;color:#9a8aaa;margin-bottom:12px}
.btn{background:var(--accent);color:white;border:none;padding:9px 16px;border-radius:30px;font-weight:700;cursor:pointer;width:100%;font-size:13.5px}
.btn:hover{opacity:.9}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:1000}
.box{background:white;padding:32px;border-radius:22px;width:90%;max-width:400px;box-shadow:0 24px 60px rgba(0,0,0,.2)}
.box h2{color:var(--accent);margin-bottom:18px;text-align:center}
input{width:100%;padding:13px;margin:7px 0;border:1px solid #eee;border-radius:12px;font-size:15px}
.hidden{display:none!important}
.section{display:none}
.section.active{display:block}
.wallet-card{background:white;border-radius:20px;padding:28px;max-width:520px;margin:0 auto;box-shadow:var(--shadow)}
.amounts{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
.amounts button{background:#fff0f7;border:none;padding:12px 20px;border-radius:14px;font-weight:700;cursor:pointer;color:var(--accent)}
.amounts button:hover{background:var(--accent);color:white}
</style>
</head>
<body>
<div id="auth" class="modal">
  <div class="box">
    <img src="https://i.imgur.com/8Km9tLL.png" style="width:90px;height:90px;border-radius:18px;object-fit:cover;display:block;margin:0 auto 12px" onerror="this.style.display='none'">
    <h2 id="atitle">Iniciar sesión</h2>
    <input id="aname" class="hidden" placeholder="Tu nombre">
    <input id="aemail" type="email" placeholder="Correo electrónico">
    <input id="apass" type="password" placeholder="Contraseña">
    <button class="btn" onclick="doAuth()" style="margin-top:10px">Continuar</button>
    <p style="text-align:center;margin-top:14px"><span id="aswitch" onclick="toggleAuth()" style="color:var(--accent);cursor:pointer;font-weight:700">¿No tienes cuenta? Regístrate</span></p>
    <p id="aerr" style="color:#ef4444;text-align:center;margin-top:8px;font-size:14px"></p>
  </div>
</div>

<div id="app" class="hidden">
  <div class="sidebar">
    <div class="logo-box">
      <img src="https://i.imgur.com/8Km9tLL.png" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect fill=%22%23ffb6d9%22 width=%22100%22 height=%22100%22 rx=%2220%22/><text x=%2250%22 y=%2265%22 font-size=%2250%22 text-anchor=%22middle%22 fill=%22white%22>G</text></svg>'">
      <div class="logo-text">GaspKe Shop</div>
    </div>
    <div class="nav active" onclick="showSec('store',this)">🛍️ Tienda</div>
    <div class="nav" onclick="showSec('accounts',this)">🎟️ Mis Cuentas</div>
    <div class="nav" onclick="showSec('wallet',this)">💰 Recargar</div>
    <div style="flex:1"></div>
    <div class="nav" onclick="logout()">🚪 Cerrar sesión</div>
  </div>
  <div class="main">
    <div class="top">
      <h1 id="greet">¡Hola!</h1>
      <div class="bal">💵 $<span id="bal">50.00</span></div>
    </div>
    <div id="store" class="section active"><div class="grid" id="store-grid"></div></div>
    <div id="accounts" class="section"><div class="grid" id="acc-grid"></div></div>
    <div id="wallet" class="section">
      <div class="wallet-card">
        <h2 style="margin-bottom:6px">Recargar saldo</h2>
        <p style="color:#9a8aaa;margin-bottom:8px">Elige un monto</p>
        <div class="amounts">
          <button onclick="recharge(10)">$10</button>
          <button onclick="recharge(25)">$25</button>
          <button onclick="recharge(50)">$50</button>
          <button onclick="recharge(100)">$100</button>
        </div>
      </div>
    </div>
  </div>
</div>
<script>
let mode='login', token=localStorage.getItem('t'), user=JSON.parse(localStorage.getItem('u')||'null');
function greet(){const h=new Date().getHours();return h<12?'Buenos días':h<19?'Buenas tardes':'Buenas noches'}
function showApp(){
  document.getElementById('auth').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
  document.getElementById('greet').textContent=greet()+', '+(user?user.name:'')+' ✨';
  document.getElementById('bal').textContent=(user?.balance||50).toFixed(2);
  loadStore();
}
function toggleAuth(){
  mode=mode==='login'?'register':'login';
  document.getElementById('atitle').textContent=mode==='login'?'Iniciar sesión':'Crear cuenta';
  document.getElementById('aname').classList.toggle('hidden',mode==='login');
  document.getElementById('aswitch').textContent=mode==='login'?'¿No tienes cuenta? Regístrate':'¿Ya tienes cuenta? Inicia sesión';
}
async function doAuth(){
  const name=document.getElementById('aname').value.trim();
  const email=document.getElementById('aemail').value.trim();
  const password=document.getElementById('apass').value;
  const err=document.getElementById('aerr'); err.textContent='';
  if(mode==='register'&&!name) return err.textContent='Nombre obligatorio';
  if(!email||!password) return err.textContent='Datos incompletos';
  const r=await fetch(mode==='register'?'/api/register':'/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(mode==='register'?{name,email,password}:{email,password})});
  const d=await r.json();
  if(!r.ok) return err.textContent=d.error||'Error';
  token=d.token; user=d.user;
  localStorage.setItem('t',token); localStorage.setItem('u',JSON.stringify(user));
  showApp();
}
function logout(){localStorage.clear();location.reload()}
function showSec(id,el){
  document.querySelectorAll('.nav').forEach(n=>n.classList.remove('active'));
  if(el) el.classList.add('active');
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  if(id==='store') loadStore();
  if(id==='accounts') loadAccounts();
}
async function loadStore(){
  const r=await fetch('/api/platforms'); const p=await r.json();
  document.getElementById('store-grid').innerHTML=p.map(x=>`
    <div class="card">
      <div class="icon" style="background:${x.color}">${x.icon}</div>
      <div class="name">${x.name}</div>
      <div class="price">$${x.price.toFixed(2)}</div>
      <div class="stock">${x.stock} disponibles</div>
      <button class="btn" onclick="buy('${x.id}','${x.name}',${x.price})">Agregar</button>
    </div>`).join('');
}
async function loadAccounts(){
  const r=await fetch('/api/accounts',{headers:{Authorization:'Bearer '+token}});
  const a=await r.json();
  document.getElementById('acc-grid').innerHTML=a.length?a.map(x=>`
    <div class="card" style="text-align:left">
      <div class="name">${x.platform}</div>
      <div style="font-size:13px;margin:8px 0;word-break:break-all">${x.email}</div>
      <div style="font-size:13px;color:#666">${x.password}</div>
      <div style="font-size:12px;color:#aaa;margin-top:8px">Vence: ${x.expires}</div>
    </div>`).join(''):'<p style="grid-column:1/-1;text-align:center;color:#9a8aaa;padding:40px">Aún no tienes cuentas</p>';
}
async function buy(id,name,price){
  if(!confirm('¿Comprar '+name+' por $'+price.toFixed(2)+'?')) return;
  const r=await fetch('/api/checkout',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({items:[{id,name,price,qty:1}]})});
  const d=await r.json();
  if(!r.ok) return alert(d.error||'Error');
  user.balance=d.balance; localStorage.setItem('u',JSON.stringify(user));
  document.getElementById('bal').textContent=d.balance.toFixed(2);
  alert('¡Comprado! Revisa Mis Cuentas');
  showSec('accounts',document.querySelectorAll('.nav')[1]);
}
async function recharge(amt){
  const r=await fetch('/api/recharge',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({amount:amt})});
  const d=await r.json();
  if(!r.ok) return alert(d.error||'Error');
  user.balance=d.balance; localStorage.setItem('u',JSON.stringify(user));
  document.getElementById('bal').textContent=d.balance.toFixed(2);
  alert('+$'+amt+' agregados');
}
if(token&&user) showApp();
</script>
</body></html>'''

@app.route('/')
def index():
    r=make_response(HTML); r.headers['Cache-Control']='no-store'; return r

@app.route('/api/register', methods=['POST'])
def register():
    d=request.json
    name,email,pw=d.get('name','').strip(),d.get('email','').strip().lower(),d.get('password','')
    if not name or not email or not pw: return jsonify(error="Datos incompletos"),400
    c=get_db()
    try:
        c.execute('INSERT INTO users (name,email,password,balance,created_at) VALUES (?,?,?,50,?)',(name,email,hash_pw(pw),datetime.now().isoformat()))
        c.commit()
        uid_=c.execute('SELECT last_insert_rowid()').fetchone()[0]
        tok=secrets.token_hex(32)
        c.execute('INSERT INTO sessions VALUES (?,?,?)',(tok,uid_,datetime.now().isoformat()))
        c.commit()
        u=c.execute('SELECT id,name,email,balance FROM users WHERE id=?',(uid_,)).fetchone()
        c.close()
        return jsonify(ok=True,token=tok,user=dict(u))
    except Exception as e:
        c.close()
        return jsonify(error="Correo ya registrado" if "UNIQUE" in str(e) else str(e)),400

@app.route('/api/login', methods=['POST'])
def login():
    d=request.json
    email,pw=d.get('email','').strip().lower(),d.get('password','')
    c=get_db()
    u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
    if not u or u['password']!=hash_pw(pw):
        c.close(); return jsonify(error="Datos incorrectos"),401
    tok=secrets.token_hex(32)
    c.execute('INSERT INTO sessions VALUES (?,?,?)',(tok,u['id'],datetime.now().isoformat()))
    c.commit(); c.close()
    return jsonify(ok=True,token=tok,user={"id":u['id'],"name":u['name'],"email":u['email'],"balance":u['balance']})

@app.route('/api/platforms')
def platforms():
    c=get_db(); rows=c.execute('SELECT * FROM platforms').fetchall(); c.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/accounts')
def accounts():
    u=uid(request.headers.get('Authorization','').replace('Bearer ',''))
    if not u: return jsonify([])
    c=get_db(); rows=c.execute('SELECT * FROM accounts WHERE user_id=? ORDER BY id DESC',(u,)).fetchall(); c.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/checkout', methods=['POST'])
def checkout():
    u=uid(request.headers.get('Authorization','').replace('Bearer ',''))
    if not u: return jsonify(error="No autenticado"),401
    items=request.json.get('items',[])
    if not items: return jsonify(error="Vacío"),400
    c=get_db()
    bal=c.execute('SELECT balance FROM users WHERE id=?',(u,)).fetchone()['balance']
    total=sum(i['price']*i.get('qty',1) for i in items)
    if bal<total: c.close(); return jsonify(error="Saldo insuficiente"),400
    newb=bal-total
    c.execute('UPDATE users SET balance=? WHERE id=?',(newb,u))
    now=datetime.now()
    for it in items:
        p=c.execute('SELECT * FROM platforms WHERE id=?',(it['id'],)).fetchone()
        if not p or p['stock']<1:
            c.rollback(); c.close(); return jsonify(error="Sin stock"),400
        c.execute('UPDATE platforms SET stock=stock-1 WHERE id=?',(it['id'],))
        em=f"user{os.urandom(2).hex()}@gaspke.shop"
        pw='Pass'+os.urandom(3).hex()+'!'
        pin=str(1000+os.urandom(1)[0]%9000)
        exp=(now+timedelta(days=30)).strftime('%d/%m/%Y')
        c.execute('INSERT INTO accounts (user_id,platform,email,password,pin,expires,bought,created_at) VALUES (?,?,?,?,?,?,?,?)',
                  (u,it['name'],em,pw,pin,exp,now.strftime('%d/%m/%Y'),now.isoformat()))
    c.execute('INSERT INTO sales (user_id,date,total,items) VALUES (?,?,?,?)',(u,now.isoformat(),total,len(items)))
    c.commit(); c.close()
    return jsonify(ok=True,balance=newb)

@app.route('/api/recharge', methods=['POST'])
def recharge():
    u=uid(request.headers.get('Authorization','').replace('Bearer ',''))
    if not u: return jsonify(error="No autenticado"),401
    amt=float(request.json.get('amount',0))
    if amt<=0: return jsonify(error="Monto inválido"),400
    c=get_db()
    c.execute('UPDATE users SET balance=balance+? WHERE id=?',(amt,u))
    c.commit()
    bal=c.execute('SELECT balance FROM users WHERE id=?',(u,)).fetchone()['balance']
    c.close()
    return jsonify(ok=True,balance=bal)

init_db()
if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
