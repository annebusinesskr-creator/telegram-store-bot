import os, json, time, sqlite3, urllib.request, urllib.parse, uuid

TOKEN = os.environ.get('BOT_TOKEN','')
ADMIN_IDS = {int(x.strip()) for x in os.environ.get('ADMIN_IDS','').split(',') if x.strip()}
DB='store.db'

PRODUCTS={
'wink':('WINK VIP',2000,'7 Hari','📖 WINK — DESKRIPSI\n━━━━━━━━━━━━━━━━━━\n\n🩵 WINK VIP / VIP+\n\n✨ Fitur:\n• Filter premium\n• Effect premium\n• Retouching tools\n• Fitur premium lainnya\n\n📱 Support Android & iOS\n\n⚠️ Catatan:\n• Jangan mengubah password akun.\n• Hubungi admin jika ada masalah.'),
'zoom':('ZOOM',5000,'30 Hari','📖 ZOOM\n\nAkses premium sesuai paket yang dipilih.'),
'hma':('HMA VPN',5000,'30 Hari','📖 HMA VPN\n\nAkses premium sesuai paket yang dipilih.'),
'express':('EXPRESSVPN',5000,'30 Hari','📖 EXPRESSVPN\n\nAkses premium sesuai paket yang dipilih.'),
'scribd':('SCRIBD',5000,'30 Hari','📖 SCRIBD\n\nAkses premium sesuai paket yang dipilih.'),
'picsart':('PICSART',5000,'30 Hari','📖 PICSART\n\nAkses premium sesuai paket yang dipilih.'),
'remini':('REMINI',5000,'30 Hari','📖 REMINI\n\nAkses premium sesuai paket yang dipilih.'),
'meitu':('MEITU',5000,'30 Hari','📖 MEITU\n\nAkses premium sesuai paket yang dipilih.'),
'outlook':('OUTLOOK',3000,'30 Hari','📖 OUTLOOK\n\nAkun sesuai stok yang tersedia.'),
'canva':('CANVA',5000,'30 Hari','📖 CANVA\n\nAkses premium sesuai paket yang dipilih.')}

conn=sqlite3.connect(DB,check_same_thread=False)
conn.execute('CREATE TABLE IF NOT EXISTS orders(order_id TEXT PRIMARY KEY,user_id INTEGER,username TEXT,product_key TEXT,product_name TEXT,duration TEXT,account_type TEXT,buyer_request TEXT,price INTEGER,payment_status TEXT,order_status TEXT,created_at TEXT)')
conn.commit()

def api(method,data=None):
    url=f'https://api.telegram.org/bot{TOKEN}/{method}'
    body=urllib.parse.urlencode(data or {}).encode()
    req=urllib.request.Request(url,body)
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read())

def send(cid,text,kb=None):
    d={'chat_id':cid,'text':text}
    if kb:d['reply_markup']=json.dumps(kb)
    return api('sendMessage',d)

def edit(cid,mid,text,kb=None):
    d={'chat_id':cid,'message_id':mid,'text':text}
    if kb:d['reply_markup']=json.dumps(kb)
    return api('editMessageText',d)

def kb(rows):return {'inline_keyboard':[[{'text':t,'callback_data':c} for t,c in r] for r in rows]}
def money(n):return 'Rp'+f'{n:,}'.replace(',','.')
def mainkb():return kb([
[('🩵 WINK','product:wink'),('💜 ZOOM','product:zoom')],
[('🩵 HMA VPN','product:hma'),('💗 EXPRESSVPN','product:express')],
[('🖤 SCRIBD','product:scribd'),('💕 PICSART','product:picsart')],
[('🌸 REMINI','product:remini'),('🎀 MEITU','product:meitu')],
[('📧 OUTLOOK','product:outlook'),('🎨 CANVA','product:canva')]])

def productkb(k):return kb([[('👤 AKUN SENDIRI',f'self:{k}')],[('✨ AKUN BARU',f'new:{k}')],[('📖 DESKRIPSI',f'desc:{k}')],[('◀️ KEMBALI','home')]])
def newkb(k):return kb([[('📝 REQUEST SESUAI KEBUTUHAN',f'request:{k}')],[('🎲 RANDOM / OTOMATIS',f'random:{k}')],[('◀️ KEMBALI',f'product:{k}')]])
def paykb(o):return kb([[('💳 BAYAR SEKARANG',f'pay:{o}')],[('🔄 CEK PEMBAYARAN',f'check:{o}')],[('❌ BATALKAN ORDER',f'cancel:{o}')]])
def adminkb(o):return kb([[('✅ SELESAIKAN',f'finish:{o}')],[('❌ TOLAK',f'reject:{o}')]])

def create_order(u,k,typ,req=''):
    p=PRODUCTS[k]; o=f'{k.upper()}-{uuid.uuid4().hex[:6].upper()}'
    conn.execute('INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?,?,?,datetime("now"))',(o,u.get('id'),u.get('username'),k,p[0],p[2],typ,req,p[1],'UNPAID','WAITING_PAYMENT'));conn.commit();return o

def order(o):
    cur=conn.execute('SELECT * FROM orders WHERE order_id=?',(o,));r=cur.fetchone();
    if not r:return None
    cols=['order_id','user_id','username','product_key','product_name','duration','account_type','buyer_request','price','payment_status','order_status','created_at'];return dict(zip(cols,r))

def notify_admin(o):
    r=order(o)
    txt=f'🔔 ORDER BARU\n\n🆔 #{o}\n👤 @{r["username"] or "-"}\n📦 {r["product_name"]}\n👤 {r["account_type"]}\n💰 {money(r["price"])}\n\n📝 Request:\n{r["buyer_request"] or "-"}'
    for a in ADMIN_IDS:
        try:send(a,txt,adminkb(o))
        except:pass

waiting={}

def handle_message(m):
    cid=m['chat']['id'];u=m.get('from',{});text=m.get('text','')
    if text=='/start':
        waiting.pop(cid,None);send(cid,'🩵 WELCOME TO ANNE STORE\n\nHalo! 👋\n\n✨ Pilih produk yang ingin kamu beli:',mainkb());return
    if text=='/cancel':waiting.pop(cid,None);send(cid,'❌ Request dibatalkan.',mainkb());return
    if cid in waiting:
        k=waiting.pop(cid);o=create_order(u,k,'AKUN BARU - REQUEST',text);p=PRODUCTS[k]
        send(cid,f'✅ REQUEST DITERIMA\n━━━━━━━━━━━━━━━━━━\n\n🆔 Order: #{o}\n📦 Produk: {p[0]}\n👤 Tipe: Akun Baru / Request\n\n📝 Request:\n{text}\n\n💰 Total: {money(p[1])}\n\nSilakan lanjut ke pembayaran.',paykb(o));return

def callback(q):
    cid=q['message']['chat']['id'];mid=q['message']['message_id'];data=q['data'];api('answerCallbackQuery',{'callback_query_id':q['id']})
    if data=='home':edit(cid,mid,'🩵 PILIH PRODUK\n\nSilakan pilih produk:',mainkb());return
    a,b=(data.split(':',1)+[''])[:2]
    if a=='product':
        p=PRODUCTS[b];edit(cid,mid,f'🩵 {p[0]}\n━━━━━━━━━━━━━━━━━━\n\n✨ Durasi: {p[2]}\n💰 Harga: {money(p[1])}\n\nSilakan pilih jenis akun:',productkb(b))
    elif a=='desc':edit(cid,mid,PRODUCTS[b][3],kb([[('◀️ KEMBALI',f'product:{b}')]]))
    elif a=='new':edit(cid,mid,'✨ AKUN BARU\n\nApakah kamu ingin menentukan sendiri email & password akun?\n\nPilih salah satu:',newkb(b))
    elif a=='request':waiting[cid]=b;edit(cid,mid,'📝 REQUEST AKUN\n━━━━━━━━━━━━━━━━━━\n\nKirim request kamu.\n\nContoh:\nEmail: anne@example.com\nPassword: Anne12345\n\nKetik /cancel untuk membatalkan.')
    elif a in ('random','self'):
        typ='AKUN BARU - RANDOM' if a=='random' else 'AKUN SENDIRI';o=create_order(q['from'],b,typ);p=PRODUCTS[b];edit(cid,mid,f'📦 ORDER\n\n🆔 #{o}\n📦 {p[0]}\n💰 {money(p[1])}\n\nLanjutkan pembayaran:',paykb(o))
    elif a=='pay':
        r=order(b);edit(cid,mid,f'💳 PEMBAYARAN\n━━━━━━━━━━━━━━━━━━\n\n🆔 #{b}\n📦 {r["product_name"]}\n💰 {money(r["price"])}\n\nSilakan transfer sesuai instruksi admin. Setelah bayar tekan Cek Pembayaran.',paykb(b))
    elif a=='check':
        r=order(b);notify_admin(b);edit(cid,mid,f'⏳ PEMBAYARAN SEDANG DIVERIFIKASI\n\n🆔 #{b}\n\nAdmin akan memproses setelah pembayaran diverifikasi.')
    elif a=='cancel':
        conn.execute('UPDATE orders SET order_status="CANCELLED" WHERE order_id=?',(b,));conn.commit();edit(cid,mid,'❌ Order dibatalkan.\n\nKetik /start untuk kembali.')
    elif a in ('finish','reject'):
        if cid not in ADMIN_IDS:return
        r=order(b)
        if a=='finish':
            conn.execute('UPDATE orders SET payment_status="PAID",order_status="PROCESSING" WHERE order_id=?',(b,));conn.commit();send(r['user_id'],f'🎉 PEMBAYARAN TERVERIFIKASI\n\n🆔 #{b}\n📦 {r["product_name"]}\n\nOrder sedang diproses admin.')
        else:
            conn.execute('UPDATE orders SET order_status="CANCELLED" WHERE order_id=?',(b,));conn.commit();send(r['user_id'],f'❌ Order #{b} ditolak/dibatalkan. Silakan hubungi admin.')

def main():
    if not TOKEN:raise SystemExit('BOT_TOKEN belum diisi di Railway Variables')
    offset=0;print('BOT RUNNING')
    while True:
        try:
            res=api('getUpdates',{'offset':offset,'timeout':50})
            for u in res.get('result',[]):
                offset=u['update_id']+1
                if 'message' in u:handle_message(u['message'])
                elif 'callback_query' in u:callback(u['callback_query'])
        except Exception as e:print('ERR',e);time.sleep(3)

if __name__=='__main__':main()
