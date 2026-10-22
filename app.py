"""
Beauty Shop - a simple online ordering app built with Streamlit.

Customers can:   browse products -> add to cart -> place an order (Cash on Delivery)
                 * FIRST order from a phone number gets FREE delivery
                 * Orders of Rs. 10,000 or more get a FREE GIFT
Admin can:       log in -> add / edit / delete products -> view orders and update status

Data is stored in a small SQLite database file (beauty_shop.db) that is created
automatically the first time the app runs.
"""

import os
import sqlite3
from datetime import datetime

import streamlit as st

# ---------------------------------------------------------------------------
# STEP 1: Basic settings  (change these numbers to change your offers)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Beauty Shop", page_icon="💄", layout="wide")

DB_FILE = os.environ.get("BEAUTY_DB_FILE", "beauty_shop.db")
CURRENCY = "Rs."
ORDER_STATUSES = ["Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"]

DELIVERY_FEE = 250            # normal delivery charge
GIFT_THRESHOLD = 10000        # products total needed to get the free gift
GIFT_NAME = "Free Gift: Luxury Beauty Pouch Set"

# Products the shop starts with. Admin can add more later from the Admin page.
# Format: (name, category, price, stock, description)
SAMPLE_PRODUCTS = [
    # Lips
    ("Velvet Matte Lipstick", "Lips", 899, 25, "Long-lasting matte finish in rose pink."),
    ("Glossy Lip Gloss", "Lips", 649, 30, "High-shine, non-sticky gloss with a juicy peach tint."),
    ("Nourishing Lip Balm", "Lips", 349, 50, "Shea butter balm for soft, smooth lips."),
    ("Lip Liner Pencil", "Lips", 399, 40, "Defines and prevents lipstick from bleeding."),
    # Eyes
    ("Volume Boost Mascara", "Eyes", 749, 30, "Dramatic volume and length, smudge-proof."),
    ("Waterproof Eyeliner", "Eyes", 499, 35, "Intense black, stays put all day."),
    ("Nude Eyeshadow Palette", "Eyes", 1799, 15, "12 blendable shades from matte to shimmer."),
    ("Brow Shaping Pencil", "Eyes", 449, 30, "Fills and shapes brows naturally."),
    # Face
    ("Silk Foundation", "Face", 1899, 12, "Medium coverage with a natural glow."),
    ("Full Coverage Concealer", "Face", 999, 25, "Hides dark circles and blemishes."),
    ("Rosy Glow Blush", "Face", 849, 22, "Silky powder blush for a fresh flush."),
    ("Setting Powder", "Face", 1099, 20, "Translucent powder for a soft-focus finish."),
    ("Illuminating Highlighter", "Face", 1299, 18, "Champagne glow for cheekbones and brow bone."),
    # Skincare
    ("Hydrating Face Cream", "Skincare", 1499, 15, "Light daily moisturiser for all skin types."),
    ("Rose Water Toner", "Skincare", 599, 40, "Refreshing alcohol-free facial toner."),
    ("Vitamin C Serum", "Skincare", 2299, 14, "Brightens dull skin and evens skin tone."),
    ("Gentle Foaming Cleanser", "Skincare", 799, 35, "Removes dirt and makeup without drying."),
    ("SPF 50 Sunscreen", "Skincare", 1399, 28, "Lightweight daily protection, no white cast."),
    ("Clay Face Mask", "Skincare", 949, 20, "Deep-cleansing mask for oily and combination skin."),
    # Hair
    ("Argan Hair Oil", "Hair", 1199, 20, "Nourishing oil for shiny, smooth hair."),
    ("Repair Shampoo", "Hair", 899, 30, "Strengthens damaged and colour-treated hair."),
    ("Deep Conditioner", "Hair", 999, 25, "Intense moisture for dry hair."),
    # Body & Nails
    ("Shea Body Lotion", "Body", 1099, 25, "24-hour moisture with a soft vanilla scent."),
    ("Rose Perfume Mist", "Body", 1599, 18, "Light floral body mist."),
    ("Gel Nail Polish - Ruby Red", "Nails", 449, 40, "Chip-resistant colour with a glossy finish."),
]


def get_admin_password():
    """Read the admin password from Streamlit secrets, or use a default for local testing."""
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        return "admin123"  # CHANGE THIS before deploying (see README.md)


# ---------------------------------------------------------------------------
# STEP 2: Database helpers
# ---------------------------------------------------------------------------
def get_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # lets us read columns by name
    return conn


def digits_only(text):
    """'0300-123 4567' -> '03001234567'. Used to recognise the same phone number."""
    return "".join(ch for ch in (text or "") if ch.isdigit())


def add_column_if_missing(cur, table, column, definition):
    """Lets an older database file be upgraded without losing data."""
    existing = [row[1] for row in cur.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def insert_missing_samples(conn):
    """Add sample products that are not in the shop yet (matched by name). Returns how many were added."""
    existing = {row["name"] for row in conn.execute("SELECT name FROM products").fetchall()}
    added = 0
    for name, category, price, stock, description in SAMPLE_PRODUCTS:
        if name not in existing:
            conn.execute(
                "INSERT INTO products (name, category, price, stock, description, image_url) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (name, category, price, stock, description, ""),
            )
            added += 1
    conn.commit()
    return added


def init_db():
    """Create the tables if they do not exist, upgrade old ones, add sample products on first run."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """CREATE TABLE IF NOT EXISTS products (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               category TEXT NOT NULL,
               price REAL NOT NULL,
               stock INTEGER NOT NULL,
               description TEXT,
               image_url TEXT
           )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS orders (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               customer_name TEXT NOT NULL,
               phone TEXT NOT NULL,
               address TEXT NOT NULL,
               total REAL NOT NULL,
               status TEXT NOT NULL,
               created_at TEXT NOT NULL,
               subtotal REAL,
               delivery_fee REAL,
               phone_key TEXT
           )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS order_items (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               order_id INTEGER NOT NULL,
               product_name TEXT NOT NULL,
               price REAL NOT NULL,
               quantity INTEGER NOT NULL
           )"""
    )

    # Upgrade an older database (from the first version of this app)
    add_column_if_missing(cur, "orders", "subtotal", "REAL")
    add_column_if_missing(cur, "orders", "delivery_fee", "REAL")
    add_column_if_missing(cur, "orders", "phone_key", "TEXT")
    for row in cur.execute("SELECT id, phone FROM orders WHERE phone_key IS NULL").fetchall():
        cur.execute("UPDATE orders SET phone_key = ? WHERE id = ?", (digits_only(row["phone"]), row["id"]))
    conn.commit()

    # Add the sample products only when the shop is empty
    count = cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        insert_missing_samples(conn)

    conn.close()


def get_products(only_in_stock=False):
    conn = get_connection()
    query = "SELECT * FROM products"
    if only_in_stock:
        query += " WHERE stock > 0"
    query += " ORDER BY category, name"
    rows = conn.execute(query).fetchall()
    conn.close()
    return rows


def get_product(product_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return row


def add_product(name, category, price, stock, description, image_url):
    conn = get_connection()
    conn.execute(
        "INSERT INTO products (name, category, price, stock, description, image_url) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, category, price, stock, description, image_url),
    )
    conn.commit()
    conn.close()


def add_sample_products():
    """Used by the admin button. Returns how many new products were added."""
    conn = get_connection()
    added = insert_missing_samples(conn)
    conn.close()
    return added


def update_product(product_id, name, category, price, stock, description, image_url):
    conn = get_connection()
    conn.execute(
        "UPDATE products SET name=?, category=?, price=?, stock=?, description=?, image_url=? "
        "WHERE id=?",
        (name, category, price, stock, description, image_url, product_id),
    )
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


# --- Offers: free first-order delivery and free gift ---------------------
def has_previous_order(phone_key, conn=None):
    """True if this phone number already placed an order (cancelled orders do not count)."""
    if len(phone_key) < 7:
        return False
    own_connection = conn is None
    if own_connection:
        conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE phone_key = ? AND status != 'Cancelled'",
        (phone_key,),
    ).fetchone()
    if own_connection:
        conn.close()
    return row[0] > 0


def calculate_charges(subtotal, is_first_order):
    """
    Work out delivery fee, gift and the final amount.
    Returns (delivery_fee, gets_gift, total_to_pay).
    """
    delivery_fee = 0 if is_first_order else DELIVERY_FEE
    gets_gift = subtotal >= GIFT_THRESHOLD
    return delivery_fee, gets_gift, subtotal + delivery_fee


def place_order(customer_name, phone, address, cart):
    """
    Save an order. Returns (order_id, None) on success or (None, error_message) on failure.
    Stock, delivery fee and gift are all worked out here again, so they can't be faked.
    """
    conn = get_connection()
    try:
        subtotal = 0
        lines = []
        for product_id, qty in cart.items():
            product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if product is None:
                return None, "A product in your cart is no longer available."
            if product["stock"] < qty:
                return None, f"Sorry, only {product['stock']} left of '{product['name']}'."
            subtotal += product["price"] * qty
            lines.append((product, qty))

        phone_key = digits_only(phone)
        first_order = not has_previous_order(phone_key, conn)
        delivery_fee, gets_gift, total = calculate_charges(subtotal, first_order)

        cur = conn.execute(
            "INSERT INTO orders (customer_name, phone, address, total, status, created_at, "
            "subtotal, delivery_fee, phone_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (customer_name, phone, address, total, "Pending",
             datetime.now().strftime("%Y-%m-%d %H:%M"), subtotal, delivery_fee, phone_key),
        )
        order_id = cur.lastrowid

        for product, qty in lines:
            conn.execute(
                "INSERT INTO order_items (order_id, product_name, price, quantity) VALUES (?, ?, ?, ?)",
                (order_id, product["name"], product["price"], qty),
            )
            conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, product["id"]))

        if gets_gift:  # the gift is saved as an item with price 0 so the admin can see it
            conn.execute(
                "INSERT INTO order_items (order_id, product_name, price, quantity) VALUES (?, ?, 0, 1)",
                (order_id, GIFT_NAME),
            )

        conn.commit()
        return order_id, None
    except Exception as error:  # keep it simple: show any problem to the user
        conn.rollback()
        return None, f"Could not place the order: {error}"
    finally:
        conn.close()


def get_orders():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def get_order_items(order_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    conn.close()
    return rows


def update_order_status(order_id, status):
    conn = get_connection()
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# STEP 3: Cart helpers (the cart lives in st.session_state)
# ---------------------------------------------------------------------------
def init_session():
    """Create the values we want to remember between button clicks."""
    if "cart" not in st.session_state:
        st.session_state.cart = {}  # {product_id: quantity}
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "last_order" not in st.session_state:
        st.session_state.last_order = None  # (order_id, got_free_delivery, got_gift)


def cart_count():
    return sum(st.session_state.cart.values())


def money(amount):
    return f"{CURRENCY} {amount:,.0f}"


# ---------------------------------------------------------------------------
# STEP 4: Customer pages
# ---------------------------------------------------------------------------
def offers_banner():
    """Short banner that tells customers about the two offers."""
    st.info(
        f"🚚 **Free delivery on your first order**  |  "
        f"🎁 **Free gift on orders of {money(GIFT_THRESHOLD)} or more**"
    )


def page_shop():
    st.title("💄 Beauty Shop")
    offers_banner()
    st.write("Browse our products and add your favourites to the cart.")

    products = get_products()
    if not products:
        st.info("No products yet. Please check back soon!")
        return

    # Category filter
    categories = ["All"] + sorted({p["category"] for p in products})
    chosen = st.selectbox("Filter by category", categories)
    search = st.text_input("Search products", placeholder="e.g. lipstick")

    shown = [
        p for p in products
        if (chosen == "All" or p["category"] == chosen)
        and search.lower() in p["name"].lower()
    ]
    if not shown:
        st.warning("No products match your search.")
        return

    # Show products in a grid of 3 columns
    columns = st.columns(3)
    for index, product in enumerate(shown):
        with columns[index % 3]:
            with st.container(border=True):
                if product["image_url"]:
                    st.image(product["image_url"])
                st.subheader(product["name"])
                st.caption(product["category"])
                st.write(product["description"] or "")
                st.write(f"**{money(product['price'])}**")

                if product["stock"] <= 0:
                    st.error("Out of stock")
                else:
                    st.caption(f"{product['stock']} in stock")
                    qty = st.number_input(
                        "Quantity",
                        min_value=1,
                        max_value=int(product["stock"]),
                        value=1,
                        key=f"qty_{product['id']}",
                    )
                    if st.button("Add to cart 🛒", key=f"add_{product['id']}"):
                        already = st.session_state.cart.get(product["id"], 0)
                        new_qty = min(already + int(qty), int(product["stock"]))
                        st.session_state.cart[product["id"]] = new_qty
                        st.toast(f"Added {product['name']} to your cart")


def page_cart():
    st.title("🛒 Your Cart")

    cart = st.session_state.cart

    # Show the confirmation after an order is placed
    if st.session_state.last_order and not cart:
        order_id, free_delivery, got_gift = st.session_state.last_order
        st.success(
            f"Thank you! Your order #{order_id} has been placed. "
            "Please keep the cash ready when it arrives (Cash on Delivery)."
        )
        if free_delivery:
            st.write("🚚 You got **free delivery** on your first order!")
        if got_gift:
            st.write(f"🎁 Your **{GIFT_NAME.replace('Free Gift: ', '')}** will arrive with your order!")
        st.balloons()
        st.session_state.last_order = None
        return

    if not cart:
        offers_banner()
        st.info("Your cart is empty. Go to the Shop page to add products.")
        return

    # List cart items
    subtotal = 0
    for product_id, qty in list(cart.items()):
        product = get_product(product_id)
        if product is None:  # product was deleted by admin
            del cart[product_id]
            st.rerun()
        line_total = product["price"] * qty
        subtotal += line_total

        col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
        col1.write(f"**{product['name']}**")
        col2.write(f"{qty} x {money(product['price'])}")
        col3.write(money(line_total))
        if col4.button("❌", key=f"remove_{product_id}", help="Remove from cart"):
            del cart[product_id]
            st.rerun()

    st.divider()

    # Delivery details (normal inputs, so the delivery fee can update as soon as a phone number is typed)
    st.subheader("Delivery details")
    name = st.text_input("Full name", key="checkout_name")
    phone = st.text_input("Phone number", key="checkout_phone")
    address = st.text_area("Delivery address", key="checkout_address")

    phone_key = digits_only(phone)
    phone_ok = len(phone_key) >= 7
    first_order = phone_ok and not has_previous_order(phone_key)
    delivery_fee, gets_gift, total = calculate_charges(subtotal, first_order)

    # Order summary
    st.divider()
    st.subheader("Order summary")
    st.write(f"Products: **{money(subtotal)}**")
    if not phone_ok:
        st.write(f"Delivery: **{money(DELIVERY_FEE)}** (enter your phone number - delivery is free on your first order)")
    elif first_order:
        st.write("Delivery: **FREE** 🚚 (first order)")
    else:
        st.write(f"Delivery: **{money(delivery_fee)}**")

    if gets_gift:
        st.success(f"🎁 You get a free gift: {GIFT_NAME.replace('Free Gift: ', '')}!")
    else:
        st.info(f"🎁 Add {money(GIFT_THRESHOLD - subtotal)} more to get a free gift (orders of {money(GIFT_THRESHOLD)} or more).")

    st.subheader(f"Total to pay: {money(total if phone_ok else subtotal + DELIVERY_FEE)}")
    st.caption("Payment method: Cash on Delivery (COD)")

    if st.button("Place order (Cash on Delivery)"):
        if not name.strip() or not phone.strip() or not address.strip():
            st.error("Please fill in your name, phone number and address.")
        elif not phone_ok:
            st.error("Please enter a valid phone number.")
        else:
            order_id, error = place_order(name.strip(), phone.strip(), address.strip(), cart)
            if error:
                st.error(error)
            else:
                st.session_state.cart = {}
                st.session_state.last_order = (order_id, delivery_fee == 0, gets_gift)
                st.rerun()


# ---------------------------------------------------------------------------
# STEP 5: Admin pages
# ---------------------------------------------------------------------------
def page_admin():
    st.title("🔐 Admin Panel")

    # --- Login ---
    if not st.session_state.is_admin:
        with st.form("login_form"):
            password = st.text_input("Admin password", type="password")
            login = st.form_submit_button("Log in")
        if login:
            if password == get_admin_password():
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Wrong password.")
        return

    if st.button("Log out"):
        st.session_state.is_admin = False
        st.rerun()

    tab_products, tab_orders = st.tabs(["📦 Products", "🧾 Orders"])

    with tab_products:
        admin_products_tab()
    with tab_orders:
        admin_orders_tab()


def admin_products_tab():
    # --- Load the ready-made sample products ---
    st.subheader("Quick add: sample products")
    st.caption(f"Adds the {len(SAMPLE_PRODUCTS)} sample beauty products. Products that already exist (same name) are skipped.")
    if st.button("➕ Add sample products"):
        added = add_sample_products()
        if added:
            st.success(f"Added {added} new products.")
            st.rerun()
        else:
            st.info("All sample products are already in your shop.")

    # --- Add a new product ---
    st.divider()
    st.subheader("Add a new product")
    with st.form("add_product_form", clear_on_submit=True):
        name = st.text_input("Product name")
        category = st.text_input("Category (e.g. Lips, Skincare, Hair)")
        price = st.number_input("Price", min_value=0.0, step=50.0)
        stock = st.number_input("Stock", min_value=0, step=1)
        description = st.text_area("Description")
        image_url = st.text_input("Image URL (optional)")
        add = st.form_submit_button("Add product")

    if add:
        if not name.strip() or not category.strip() or price <= 0:
            st.error("Please enter a name, a category and a price above 0.")
        else:
            add_product(name.strip(), category.strip(), price, int(stock),
                        description.strip(), image_url.strip())
            st.success(f"Added '{name}'.")
            st.rerun()

    # --- Edit / delete existing products ---
    st.divider()
    st.subheader("Edit or delete products")
    products = get_products()
    if not products:
        st.info("No products yet.")
        return

    for product in products:
        label = f"{product['name']}  -  {money(product['price'])}  -  stock: {product['stock']}"
        with st.expander(label):
            with st.form(f"edit_form_{product['id']}"):
                name = st.text_input("Name", product["name"])
                category = st.text_input("Category", product["category"])
                price = st.number_input("Price", min_value=0.0, value=float(product["price"]), step=50.0)
                stock = st.number_input("Stock", min_value=0, value=int(product["stock"]), step=1)
                description = st.text_area("Description", product["description"] or "")
                image_url = st.text_input("Image URL", product["image_url"] or "")
                save = st.form_submit_button("Save changes")
            if save:
                if not name.strip() or not category.strip() or price <= 0:
                    st.error("Name, category and a price above 0 are required.")
                else:
                    update_product(product["id"], name.strip(), category.strip(), price,
                                   int(stock), description.strip(), image_url.strip())
                    st.success("Saved.")
                    st.rerun()

            if st.button("🗑️ Delete this product", key=f"delete_{product['id']}"):
                delete_product(product["id"])
                st.rerun()


def admin_orders_tab():
    st.subheader("Customer orders")
    orders = get_orders()
    if not orders:
        st.info("No orders yet.")
        return

    # Simple filter by status
    status_filter = st.selectbox("Show orders", ["All"] + ORDER_STATUSES)

    for order in orders:
        if status_filter != "All" and order["status"] != status_filter:
            continue

        title = f"Order #{order['id']} - {order['customer_name']} - {money(order['total'])} - {order['status']}"
        with st.expander(title):
            st.write(f"**Date:** {order['created_at']}")
            st.write(f"**Phone:** {order['phone']}")
            st.write(f"**Address:** {order['address']}")
            st.write("**Payment:** Cash on Delivery")

            st.write("**Items:**")
            for item in get_order_items(order["id"]):
                if item["price"] == 0:
                    st.write(f"- 🎁 {item['product_name']} (x{item['quantity']})")
                else:
                    st.write(f"- {item['product_name']} - {item['quantity']} x {money(item['price'])}")

            # Older orders (from before the offers existed) have no subtotal / delivery fee saved
            subtotal = order["subtotal"] if order["subtotal"] is not None else order["total"]
            fee = order["delivery_fee"] if order["delivery_fee"] is not None else 0
            st.write(f"**Products:** {money(subtotal)}")
            st.write(f"**Delivery:** {'FREE' if fee == 0 else money(fee)}")
            st.write(f"**Total to collect (COD):** {money(order['total'])}")

            new_status = st.selectbox(
                "Status",
                ORDER_STATUSES,
                index=ORDER_STATUSES.index(order["status"]),
                key=f"status_{order['id']}",
            )
            if st.button("Update status", key=f"update_status_{order['id']}"):
                update_order_status(order["id"], new_status)
                st.rerun()


# ---------------------------------------------------------------------------
# STEP 6: Main - sidebar menu decides which page to show
# ---------------------------------------------------------------------------
def main():
    init_db()
    init_session()

    st.sidebar.title("💄 Beauty Shop")
    # The option values stay fixed; only the *displayed* label shows the cart count.
    # (If the values themselves changed, Streamlit would reset the menu to "Shop".)
    page = st.sidebar.radio(
        "Menu",
        ["Shop", "Cart", "Admin"],
        format_func=lambda option: f"Cart ({cart_count()})" if option == "Cart" else option,
        key="menu",
    )

    if page == "Shop":
        page_shop()
    elif page == "Cart":
        page_cart()
    else:
        page_admin()


main()
