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
    conn = sqlite3.connect("database/data_source.db")
    cursor = conn.cursor()
    
    # Grab up to 7 products that have images
    cursor.execute("SELECT product_id, image FROM product_data WHERE image IS NOT NULL LIMIT 7")
    products = cursor.fetchall()
    conn.close()

    return render_template(
        "index.html", 
        first_name=session.get("first_name"), 
        products=products
    )

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
        print ('invalid login')


@app.route("/signup", methods=["POST"])
def signup():
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    phone = request.form["phone"]
    password = request.form["password"]
    street_number = request.form["street_number"]
    street_name = request.form["street_name"]
    street_suffix = request.form["street_suffix"]
    suburb = request.form["suburb"]
    state = request.form["state"]

    
    conn = sqlite3.connect("database/data_source.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO Customer_Data 
        (first_name, last_name, phone, password, street_number, street_name, street_suffix, suburb, state)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (first_name, last_name, phone, password, street_number, street_name, street_suffix, suburb, state))

    conn.commit()
    conn.close()
    

    # Auto-login
    session["phone"] = phone
    session["first_name"] = first_name

    flash("Account created successfully!", "success")
    return redirect(url_for("home"))

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=5000)
