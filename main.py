from flask import Flask
from flask import render_template
from flask import request, session, redirect, url_for, flash
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def check_login(phone, password):
    conn = sqlite3.connect("database/data_source.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT password FROM Customer_Data WHERE phone = ?", (phone,))
    result = cursor.fetchone()
    conn.close()
    print("Phone",phone,"and correct password", result,"vs entered password",password)
    if result:
        stored_password = result[0]
        return password == stored_password #assuming stored_password not encrypted
        #return hashlib.sha256(password.encode()).hexdigest() == stored_password
    else:
        return False


def get_first_name(phone):
    conn = sqlite3.connect("database/data_source.db")
    cursor = conn.cursor()

    cursor.execute("SELECT first_name FROM Customer_Data WHERE phone = ?", (phone,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]  # the first_name
    return None





@app.route("/")
def home():
    return render_template("index.html", first_name=session.get("first_name"))

@app.route('/index.html', methods=['GET'])
@app.route('/', methods=['POST', 'GET'])
def index():
   return render_template('/index.html', first_name=session.get("first_name"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route('/sign_in.html', methods=['GET'])
@app.route('/', methods=['POST', 'GET'])
def sign_in():
   return render_template('/sign_in.html', content='data')

@app.route('/sign_up.html', methods=['GET'])
@app.route('/', methods=['POST', 'GET'])
def sign_up():
   return render_template('/sign_up.html', content='data')

@app.route("/login", methods=["POST"])
def login():
    phone = request.form["phone"]
    password = request.form["password"]

    if check_login(phone, password):
        session["phone"] = phone
        session["first_name"] = get_first_name(phone)  #store first name
        return redirect(url_for("home"))
    else:
        return "Invalid login"


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=5000)