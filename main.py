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

# FIRST NAME
@app.context_processor
def inject_user():
    first_name = session.get("first_name")
    return dict(first_name=first_name)


# Product Page
@app.route("/product/<int:product_id>")
def product_page(product_id):
    import sqlite3
    from flask import session

    conn = sqlite3.connect("database/data_source.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT product_id, brand, tool_name, price, amount_available, image
        FROM product_data
        WHERE product_id = ?
    """, (product_id,))
    product = cursor.fetchone()

    if not product:
        conn.close()
        return f"<h1>Product {product_id} not found.</h1>", 404

    product_info = {
        "product_id": product[0],
        "brand": product[1],
        "tool_name": product[2],
        "price": float(product[3]) if product[3] is not None else 0.0,
        "amount_available": product[4],
        "image": product[5]
    }

    # Check if user already has this product in their cart
    existing_quantity = 0
    if "phone" in session:
        user_phone = session["phone"]
        cursor.execute("""
            SELECT quantity FROM order_data
            WHERE user_number = ? AND product = ?
        """, (user_phone, product_id))
        result = cursor.fetchone()
        print("User phone in session:", session.get("phone"))
        if result:
            existing_quantity = result[0]

    conn.close()
    return render_template("product.html", product=product_info, existing_quantity=existing_quantity)

# Add to cart but its add to the order table mb
@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    import sqlite3
    from flask import session, request, jsonify

    print("DEBUG add_to_cart: Route called")
    print(f"DEBUG add_to_cart: Session contents: {session}")
    
    if "phone" not in session:
        print("DEBUG add_to_cart: No phone in session")
        return jsonify({"status": "not_signed_in"})

    data = request.get_json()
    print(f"DEBUG add_to_cart: Received data: {data}")
    
    product_id = int(data.get("product_id"))
    quantity = int(data.get("quantity"))
    user_phone = session["phone"]

    print(f"DEBUG add_to_cart: user_phone={user_phone}, product_id={product_id}, quantity={quantity}")

    conn = sqlite3.connect("database/data_source.db")
    cursor = conn.cursor()

    # 1️ Get available stock
    cursor.execute("SELECT amount_available FROM product_data WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        print(f"DEBUG add_to_cart: Product {product_id} not found")
        conn.close()
        return jsonify({"status": "product_not_found"})

    available = product[0]
    print(f"DEBUG add_to_cart: Available stock: {available}")

    # 2️ Get existing quantity in cart (if there is any)
    cursor.execute("""
        SELECT quantity FROM order_data
        WHERE user_number = ? AND product = ?
    """, (user_phone, product_id))
    existing = cursor.fetchone()
    print(f"DEBUG add_to_cart: Existing cart entry: {existing}")

    if existing:
        old_quantity = existing[0]
        diff = quantity - old_quantity  # positive if increasing, negative if reducing

        print(f"DEBUG add_to_cart: Updating - old_quantity={old_quantity}, diff={diff}")

        # Prevent over-ordering
        if diff > available:
            print(f"DEBUG add_to_cart: Exceeds stock - diff={diff}, available={available}")
            conn.close()
            return jsonify({"status": "exceeds_stock"})

        # 3️ Update order quantity
        cursor.execute("""
            UPDATE order_data
            SET quantity = ?
            WHERE user_number = ? AND product = ?
        """, (quantity, user_phone, product_id))

        # 4️ Update stock correctly
        new_available = available - diff
        cursor.execute("""
            UPDATE product_data
            SET amount_available = ?
            WHERE product_id = ?
        """, (new_available, product_id))

        conn.commit()
        print(f"DEBUG add_to_cart: Updated successfully - new_available={new_available}")
        conn.close()
        return jsonify({"status": "updated", "remaining": new_available})

    else:
        # 5️ New cart entry
        print(f"DEBUG add_to_cart: Creating new cart entry")
        
        if quantity > available:
            print(f"DEBUG add_to_cart: Exceeds stock - quantity={quantity}, available={available}")
            conn.close()
            return jsonify({"status": "exceeds_stock"})

        cursor.execute("""
            INSERT INTO order_data (user_number, product, quantity)
            VALUES (?, ?, ?)
        """, (user_phone, product_id, quantity))

        # 6️ Update available stock
        new_available = available - quantity
        cursor.execute("""
            UPDATE product_data
            SET amount_available = ?
            WHERE product_id = ?
        """, (new_available, product_id))

        conn.commit()
        print(f"DEBUG add_to_cart: Added successfully - new_available={new_available}")
        
        # Verify it was actually inserted
        cursor.execute("""
            SELECT * FROM order_data
            WHERE user_number = ? AND product = ?
        """, (user_phone, product_id))
        verify = cursor.fetchone()
        print(f"DEBUG add_to_cart: Verification after insert: {verify}")
        
        conn.close()
        return jsonify({"status": "added", "remaining": new_available})


# REMOVE FROM CAT BUTTON
@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    import sqlite3
    from flask import session, request, jsonify

    if "phone" not in session:
        return jsonify({"status": "not_signed_in"})

    data = request.get_json()
    product_id = int(data.get("product_id"))
    user_phone = session["phone"]

    conn = sqlite3.connect("database/data_source.db")
    cursor = conn.cursor()

    # 1️ Get the quantity currently in cart
    cursor.execute("""
        SELECT quantity FROM order_data
        WHERE user_number = ? AND product = ?
    """, (user_phone, product_id))
    existing = cursor.fetchone()

    if not existing:
        conn.close()
        return jsonify({"status": "not_in_cart"})

    quantity_in_cart = existing[0]

    # 2️ Delete from order_data
    cursor.execute("""
        DELETE FROM order_data
        WHERE user_number = ? AND product = ?
    """, (user_phone, product_id))

    # 3 Update available stock
    cursor.execute("""
        SELECT amount_available FROM product_data
        WHERE product_id = ?
    """, (product_id,))
    available = cursor.fetchone()[0] or 0

    new_available = available + quantity_in_cart
    cursor.execute("""
        UPDATE product_data
        SET amount_available = ?
        WHERE product_id = ?
    """, (new_available, product_id))

    conn.commit()
    conn.close()

    return jsonify({"status": "removed", "remaining": new_available})


# Makita Products Page
@app.route("/makita")
def makita_page():
    conn = sqlite3.connect("database/data_source.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT product_id, tool_name, price, image
        FROM product_data
        WHERE brand = 'Makita'
    """)
    products = cursor.fetchall()
    conn.close()

    product_list = []
    for p in products:
        product_list.append({
            "product_id": p[0],
            "tool_name": p[1],
            "price": float(p[2]) if p[2] else 0.00,
            "image": p[3]
        })

    return render_template("makita.html", products=product_list)

#Milwaukee
@app.route("/milwaukee")
def milwaukee_page():
    conn = sqlite3.connect("database/data_source.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT product_id, brand, tool_name, price, amount_available, image
        FROM product_data
        WHERE brand = 'Milwaukee'
    """)
    products = cursor.fetchall()
    conn.close()

    # Convert tuples into dictionaries
    product_list = [
        {
            "product_id": p[0],
            "brand": p[1],
            "tool_name": p[2],
            "price": float(p[3]),
            "amount_available": p[4],
            "image": p[5]
        } for p in products
    ]

    return render_template("milwaukee.html", products=product_list)

#CART
#CART
@app.route("/cart")
def cart():
    import sqlite3
    from flask import session, render_template, redirect, url_for

    # Debug: Check if user is logged in
    if "phone" not in session:
        print("DEBUG CART: No phone in session")
        return redirect(url_for("sign_in"))

    user_phone = session["phone"]
    print(f"DEBUG CART: User phone from session: {user_phone}")

    conn = sqlite3.connect("database/data_source.db")
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()

    # Debug: Check what's in order_data for this user
    cursor.execute("""
        SELECT * FROM order_data WHERE user_number = ?
    """, (user_phone,))
    debug_orders = cursor.fetchall()
    print(f"DEBUG CART: Orders found for {user_phone}: {len(debug_orders)}")
    for order in debug_orders:
        print(f"DEBUG CART: Order - product: {order['product']}, quantity: {order['quantity']}")

    # Debug: Check if products exist in product_data
    cursor.execute("""
        SELECT DISTINCT od.product 
        FROM order_data od
        WHERE od.user_number = ?
    """, (user_phone,))
    cart_products = cursor.fetchall()
    print(f"DEBUG CART: Products in cart: {[p['product'] for p in cart_products]}")
    
    # Check data types
    for prod_id in cart_products:
        cursor.execute("SELECT product_id, typeof(product_id) FROM product_data WHERE product_id = ?", (prod_id['product'],))
        exists = cursor.fetchone()
        if exists:
            print(f"DEBUG CART: Product {prod_id['product']} (type: {type(prod_id['product'])}) -> product_data has {exists[0]} (type: {exists[1]})")
    
    cursor.execute("""
        SELECT od.product, od.quantity, pd.product_id, pd.tool_name
        FROM order_data od
        LEFT JOIN product_data pd ON CAST(od.product AS INTEGER) = CAST(pd.product_id AS INTEGER)
        WHERE od.user_number = ?
    """, (user_phone,))
    test_rows = cursor.fetchall()
    print(f"DEBUG CART: Test LEFT JOIN results: {len(test_rows)}")
    if test_rows:
        for tr in test_rows[:2]:  # Just show first 2
            print(f"DEBUG CART: Test row - od.product={dict(tr)}")
    
    # Fetch all cart items for this user with JOIN
    cursor.execute("""
        SELECT od.product AS product_id, od.quantity, 
               pd.tool_name, pd.brand, pd.price, pd.image
        FROM order_data od
        JOIN product_data pd ON CAST(od.product AS INTEGER) = CAST(pd.product_id AS INTEGER)
        WHERE od.user_number = ?
    """, (user_phone,))
    
    rows = cursor.fetchall()
    print(f"DEBUG CART: Rows after JOIN with CAST: {len(rows)}")
    
    # Debug: Print what columns we got
    if rows:
        print(f"DEBUG CART: First row keys: {rows[0].keys()}")
    
    conn.close()

    items = []
    total_price = 0.0

    for row in rows:
        print(f"DEBUG CART: Processing row - product_id: {row['product_id']}, quantity: {row['quantity']}")
        quantity = int(row["quantity"])
        price = float(row["price"]) if row["price"] is not None else 0.0
        total_item_price = quantity * price
        total_price += total_item_price

        items.append({
            "product_id": row["product_id"],
            "tool_name": row["tool_name"],
            "brand": row["brand"],
            "price": price,
            "image": row["image"],
            "quantity": quantity,
            "total_item_price": total_item_price
        })

    print(f"DEBUG CART: Total items to display: {len(items)}")
    print(f"DEBUG CART: Total price: {total_price}")

    return render_template("cart.html", items=items, total_price=total_price, first_name=session.get("first_name"))


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
