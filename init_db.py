import sqlite3, hashlib
DB='stato_uso.db'; conn=sqlite3.connect(DB); c=conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS veicoli (id INTEGER PRIMARY KEY AUTOINCREMENT, datetime TEXT, marca TEXT, modello TEXT, targa TEXT, data_immatricolazione TEXT, km_attuali INTEGER, spese_ripristino REAL, nome_venditore TEXT)")
pw=hashlib.sha256('admin123'.encode()).hexdigest()
c.execute("SELECT * FROM users WHERE username=?",('admin',))
if not c.fetchone(): c.execute("INSERT INTO users (username,password) VALUES (?,?)",('admin',pw))
conn.commit(); conn.close(); print('DB pronto')
