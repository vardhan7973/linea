# linea_app.py
import streamlit as st
import mysql.connector
from PIL import Image

# --- MySQL Connection ---
conn = mysql.connector.connect(
    host=st.secrets["mysql"]["host"],
    user=st.secrets["mysql"]["user"],
    password=st.secrets["mysql"]["password"],
    database=st.secrets["mysql"]["database"]
)
cursor = conn.cursor()

# --- DB Setup ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    price FLOAT,
    image_url TEXT
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_id INT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
''')
conn.commit()

# --- Session State for Login ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- UI Functions ---
def login():
    st.title("🔐 Login to Linéa")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        if user:
            st.success("Login successful")
            st.session_state.user = user[0]  # store user ID
        else:
            st.error("Invalid credentials")

def signup():
    st.title("📝 Signup for Linéa")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Signup"):
        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
            conn.commit()
            st.success("Signup successful. Please log in.")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

def view_products():
    st.title("🛍️ Linéa Products")
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    for pid, name, price, img_url in products:
        st.image(img_url, width=200)
        st.write(f"**{name}**")
        st.write(f"💸 ${price:.2f}")
        if st.button(f"Add to Cart - {pid}"):
            if st.session_state.user:
                cursor.execute("INSERT INTO cart (user_id, product_id) VALUES (%s, %s)", (st.session_state.user, pid))
                conn.commit()
                st.success("Added to cart")
            else:
                st.warning("Login to add to cart")

def view_cart():
    st.title("🛒 Your Cart")
    if st.session_state.user:
        cursor.execute('''
            SELECT p.name, p.price FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = %s
        ''', (st.session_state.user,))
        items = cursor.fetchall()
        total = sum([item[1] for item in items])
        for name, price in items:
            st.write(f"{name} - ${price:.2f}")
        st.write(f"**Total: ${total:.2f}**")
        if st.button("Checkout"):
            cursor.execute("DELETE FROM cart WHERE user_id = %s", (st.session_state.user,))
            conn.commit()
            st.success("Thank you for your purchase!")
    else:
        st.warning("Login to view cart")

# --- Navigation ---
menu = st.sidebar.selectbox("Navigation", ["Login", "Signup", "View Products", "Cart"])

if menu == "Login":
    login()
elif menu == "Signup":
    signup()
elif menu == "View Products":
    view_products()
elif menu == "Cart":
    view_cart()
