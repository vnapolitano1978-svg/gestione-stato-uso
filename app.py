# app.py
from flask import Flask, request, jsonify, send_file, send_from_directory, abort
from flask_cors import CORS
import sqlite3, hashlib, os, io, csv
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rcanvas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'stato_uso.db')

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    username, password = data.get('username'), data.get('password')
    if not username or not password:
        return jsonify({"error":"missing"}), 400
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT password FROM users WHERE username=?", (username,))
    row=cur.fetchone(); conn.close()
    if row and hash_pw(password)==row['password']:
        return jsonify({"ok":True,"token":username})
    return jsonify({"ok":False}),401

def require_token():
    if not request.headers.get('X-Auth-User'): abort(401)

@app.route('/api/records', methods=['GET'])
def list_records():
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT * FROM veicoli ORDER BY datetime DESC")
    rows=[dict(r) for r in cur.fetchall()]; conn.close()
    return jsonify(rows)

@app.route('/api/records', methods=['POST'])
def create_record():
    require_token(); data=request.json or {}
    fields=('datetime','marca','modello','targa','data_immatricolazione','km_attuali','spese_ripristino','nome_venditore')
    values=[data.get(f) for f in fields]
    if not values[0]: values[0]=datetime.now().strftime('%d-%m-%Y %H:%M')
    conn=get_conn(); cur=conn.cursor()
    cur.execute("""INSERT INTO veicoli (datetime,marca,modello,targa,data_immatricolazione,km_attuali,spese_ripristino,nome_venditore)
                 VALUES (?,?,?,?,?,?,?,?)""", values)
    conn.commit(); rid=cur.lastrowid; conn.close()
    return jsonify({"id":rid}),201

@app.route('/api/records/<int:rid>', methods=['PUT'])
def update_record(rid):
    require_token(); data=request.json or {}
    conn=get_conn(); cur=conn.cursor()
    cur.execute("""UPDATE veicoli SET datetime=?,marca=?,modello=?,targa=?,data_immatricolazione=?,km_attuali=?,spese_ripristino=?,nome_venditore=? WHERE id=?""",                    (data.get('datetime'),data.get('marca'),data.get('modello'),data.get('targa'),data.get('data_immatricolazione'),data.get('km_attuali'),data.get('spese_ripristino'),data.get('nome_venditore'),rid))
    conn.commit(); conn.close(); return jsonify({"ok":True})

@app.route('/api/records/<int:rid>', methods=['DELETE'])
def delete_record(rid):
    require_token()
    conn=get_conn(); cur=conn.cursor()
    cur.execute("DELETE FROM veicoli WHERE id=?", (rid,))
    conn.commit(); conn.close(); return jsonify({"ok":True})

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    require_token()
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT * FROM veicoli ORDER BY datetime DESC")
    rows=cur.fetchall(); conn.close()
    output=io.StringIO(); writer=csv.writer(output)
    if rows: writer.writerow(rows[0].keys())
    for r in rows: writer.writerow(list(r))
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), as_attachment=True, download_name='export.csv', mimetype='text/csv')

@app.route('/api/export/pdf', methods=['GET'])
def export_pdf():
    require_token()
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT * FROM veicoli ORDER BY datetime DESC")
    rows=[dict(r) for r in cur.fetchall()]; conn.close()
    buf=io.BytesIO(); c=rcanvas.Canvas(buf,pagesize=A4)
    w,h=A4; y=h-40; c.setFont("Helvetica",12)
    for r in rows:
        line=f"{r['datetime']} {r['marca']} {r['modello']} {r['targa']} KM:{r['km_attuali']} €{r['spese_ripristino']} {r['nome_venditore']}"
        c.drawString(30,y,line[:100]); y-=14
        if y<40: c.showPage(); y=h-40
    c.save(); buf.seek(0)
    return send_file(buf,as_attachment=True,download_name='report.pdf',mimetype='application/pdf')

@app.route('/')
def index(): return send_from_directory(app.static_folder,'index.html')

if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000)
