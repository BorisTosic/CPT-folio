import sqlite3 as sql

def listExtension():
  con = sql.connect("Flask_PWA_Programming_For_The_Web_Task_Template/database/data_source.db")
  cur = con.cursor()
  data = cur.execute('SELECT * FROM extension').fetchall()
  con.close()
  return data