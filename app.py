from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import sqlite3
from pathlib import Path

DB = Path(__file__).with_name('pokevault.db')
app = FastAPI(title='PokeVault Prototype')

def connection():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

with connection() as db:
    db.execute('CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)')
    db.execute('''CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY, profile_id INTEGER NOT NULL, name TEXT NOT NULL,
        set_name TEXT NOT NULL DEFAULT '', card_number TEXT NOT NULL DEFAULT '',
        variant TEXT NOT NULL DEFAULT 'Normal', condition TEXT NOT NULL DEFAULT 'Near Mint',
        quantity INTEGER NOT NULL DEFAULT 1, market_price REAL,
        FOREIGN KEY(profile_id) REFERENCES profiles(id))''')

class Profile(BaseModel):
    name: str = Field(min_length=1, max_length=60)

class Card(BaseModel):
    profile_id: int
    name: str = Field(min_length=1, max_length=120)
    set_name: str = Field(default='', max_length=120)
    card_number: str = Field(default='', max_length=40)
    variant: str = Field(default='Normal', max_length=50)
    condition: str = Field(default='Near Mint', max_length=50)
    quantity: int = Field(default=1, ge=1, le=9999)

@app.get('/api/profiles')
def profiles():
    with connection() as db:
        return [dict(r) for r in db.execute('SELECT * FROM profiles ORDER BY name')]

@app.post('/api/profiles')
def add_profile(item: Profile):
    with connection() as db:
        try:
            cursor = db.execute('INSERT INTO profiles(name) VALUES (?)', (item.name.strip(),))
        except sqlite3.IntegrityError:
            raise HTTPException(409, 'That profile already exists')
        return {'id': cursor.lastrowid}

@app.get('/api/cards')
def cards(profile_id: int):
    with connection() as db:
        return [dict(r) for r in db.execute('SELECT * FROM cards WHERE profile_id=? ORDER BY id DESC', (profile_id,))]

@app.post('/api/cards')
def add_card(item: Card):
    with connection() as db:
        if not db.execute('SELECT id FROM profiles WHERE id=?', (item.profile_id,)).fetchone():
            raise HTTPException(404, 'Profile not found')
        cursor = db.execute('''INSERT INTO cards(profile_id,name,set_name,card_number,variant,condition,quantity)
            VALUES(?,?,?,?,?,?,?)''', (item.profile_id,item.name.strip(),item.set_name.strip(),item.card_number.strip(),item.variant,item.condition,item.quantity))
        return {'id': cursor.lastrowid}

@app.delete('/api/cards/{card_id}')
def delete_card(card_id: int):
    with connection() as db:
        result = db.execute('DELETE FROM cards WHERE id=?', (card_id,))
        if not result.rowcount:
            raise HTTPException(404, 'Card not found')
        return {'ok': True}

HTML = '''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PokéVault</title><style>
*{box-sizing:border-box}body{font-family:system-ui;background:#10121b;color:#f2f3fa;max-width:650px;margin:auto;padding:20px}
h1{color:#b7a2ff}section{background:#1c2030;border-radius:16px;padding:16px;margin:16px 0}
input,select,button{width:100%;padding:12px;margin:6px 0;border-radius:9px;border:1px solid #555a73;font:inherit}
input,select{background:#111522;color:white}button{background:#7962d8;color:white;border:0;font-weight:700}
.row{display:flex;gap:8px}.row>*{flex:1;min-width:0}.item{padding:12px 0;border-bottom:1px solid #393e52}
.small{font-size:13px;color:#b6bbcc}.danger{background:#6e3547;width:auto;padding:7px 12px;float:right}
</style></head><body><h1>🎴 PokéVault</h1><p>Family collection • prototype 0.1</p>
<section><h3>Family member</h3><select id="profile" onchange="loadCards()"></select>
<div class="row"><input id="newProfile" placeholder="New family member"><button onclick="addProfile()">Add member</button></div></section>
<section><h3>Add a card</h3><form id="cardForm">
<input id="name" required placeholder="Card name (e.g. Pikachu)">
<div class="row"><input id="set_name" placeholder="Set"><input id="card_number" placeholder="Number (e.g. 025/198)"></div>
<div class="row"><select id="variant"><option>Normal</option><option>Holo</option><option>Reverse Holo</option><option>Other</option></select>
<select id="condition"><option>Near Mint</option><option>Lightly Played</option><option>Moderately Played</option><option>Heavily Played</option><option>Damaged</option></select></div>
<input id="quantity" type="number" min="1" max="9999" value="1" required>
<button type="submit">Save card & add next</button></form><p class="small">Camera recognition and daily pricing are coming in later phases. Prices are not estimated or fabricated.</p></section>
<section><h3>Collection <span id="count"></span></h3><div id="cards"></div></section>
<script>
const $=id=>document.getElementById(id);
async function request(path,options){const r=await fetch(path,options);if(!r.ok)throw Error((await r.json()).detail||'Request failed');return r.json()}
async function loadProfiles(selected){let list=await request('/api/profiles');$('profile').replaceChildren();for(let p of list){let o=new Option(p.name,p.id);$('profile').add(o)}if(selected)$('profile').value=selected;await loadCards()}
async function addProfile(){let name=$('newProfile').value.trim();if(!name)return;try{let p=await request('/api/profiles',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});$('newProfile').value='';await loadProfiles(p.id)}catch(e){alert(e.message)}}
async function loadCards(){let id=$('profile').value;$('cards').replaceChildren();if(!id){$('count').textContent='';return}let data=await request('/api/cards?profile_id='+encodeURIComponent(id));$('count').textContent='('+data.reduce((n,c)=>n+c.quantity,0)+' cards)';for(let c of data){let d=document.createElement('div');d.className='item';let b=document.createElement('button');b.className='danger';b.textContent='Delete';b.onclick=async()=>{if(confirm('Delete this entry?')){await request('/api/cards/'+c.id,{method:'DELETE'});loadCards()}};let title=document.createElement('strong');title.textContent=c.name+' ×'+c.quantity;let sub=document.createElement('div');sub.className='small';sub.textContent=[c.set_name,c.card_number,c.variant,c.condition].filter(Boolean).join(' · ');d.append(b,title,sub);$('cards').append(d)}}
$('cardForm').onsubmit=async e=>{e.preventDefault();if(!$('profile').value)return alert('Add a family member first');let data={profile_id:Number($('profile').value)};for(let k of ['name','set_name','card_number','variant','condition'])data[k]=$(k).value;data.quantity=Number($('quantity').value);try{await request('/api/cards',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});$('name').value='';$('card_number').value='';$('quantity').value=1;await loadCards();$('name').focus()}catch(err){alert(err.message)}};
loadProfiles();
</script></body></html>'''

@app.get('/', response_class=HTMLResponse)
def home():
    return HTML
