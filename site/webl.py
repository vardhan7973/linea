import streamlit as st
import mysql.connector
from PIL import Image

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="trojan@178",
        database="linea_db"
    )

def signup(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()
    conn.close()

def login(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def load_products():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return products

def add_to_cart(user_id, product_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cart (user_id, product_id) VALUES (%s, %s)", (user_id, product_id))
    conn.commit()
    conn.close()

def load_cart(user_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT cart.id as cart_id, products.id as product_id, products.name, products.price, products.image_url
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = %s
    """, (user_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def checkout_cart(user_id):
    cart_items = load_cart(user_id)
    total_price = sum(item['price'] for item in cart_items)

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (user_id, total_price) VALUES (%s, %s)", (user_id, total_price))
    order_id = cursor.lastrowid

    for item in cart_items:
        cursor.execute("INSERT INTO order_items (order_id, product_id) VALUES (%s, %s)", (order_id, item['product_id']))

    cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()
    return order_id, total_price

def show_product_ui():
    st.subheader("💫Elegance in every thread")
    search = st.text_input("Search Products")
    products = load_products()

    cols = st.columns(3)
    for idx, product in enumerate(products):
        if search.lower() in product['name'].lower():
            with cols[idx % 3]:
                st.image(product['image_url'], width=200)
                st.write(f"**{product['name']}**")
                st.write(f"Price: ₹{product['price']}")
                if st.button("Add to Cart", key=f"add_{product['id']}"):
                    if 'user_id' in st.session_state:
                        add_to_cart(st.session_state['user_id'], product['id'])
                        st.success("Added to cart!")
                    else:
                        st.warning("Login required")

def show_cart_ui():
    st.subheader("🛒 Your Cart")
    if 'user_id' not in st.session_state:
        st.warning("Please login to view cart")
        return

    cart_items = load_cart(st.session_state['user_id'])
    if not cart_items:
        st.info("Your cart is empty.")
        return

    total = 0
    for item in cart_items:
        st.image(item['image_url'], width=100)
        st.write(f"**{item['name']}** — ₹{item['price']}")
        total += item['price']
        st.markdown("---")

    st.write(f"### Total: ₹{total:.2f}")
    if st.button("✅ Confirm Checkout"):
        order_id, total_paid = checkout_cart(st.session_state['user_id'])
        st.success(f"Order #{order_id} placed successfully! Total paid: ₹{total_paid:.2f}")

def login_ui():
    st.subheader("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login(username, password)
        if user:
            st.session_state['user_id'] = user[0]
            st.success("Logged in!")
        else:
            st.error("Invalid credentials")

def signup_ui():
    st.subheader("📝 Signup")
    username = st.text_input("New Username")
    password = st.text_input("New Password", type="password")
    if st.button("Signup"):
        signup(username, password)
        st.success("Account created! Now login.")

# Main
st.title("Linéa Clothing")
menu = ["Home", "Login", "Signup", "Cart"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Login":
    login_ui()
elif choice == "Signup":
    signup_ui()
elif choice == "Cart":
    show_cart_ui()
else:
    show_product_ui()
