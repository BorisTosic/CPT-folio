import sqlite3 as sql

def listExtension():
  con = sql.connect("Flask_PWA_Programming_For_The_Web_Task_Template/database/data_source.db")
  cur = con.cursor()
  data = cur.execute('SELECT * FROM extension').fetchall()
  con.close()
  return data

import sqlite3, hashlib

conn = sqlite3.connect("Customer_Data.db")
cursor = conn.cursor()

phone = "0412345678"
password = hashlib.sha256("mypassword".encode()).hexdigest()

cursor.execute("INSERT INTO users (phone, password) VALUES (?, ?)", (phone, password))
conn.commit()
conn.close()