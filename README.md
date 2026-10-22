# 💄 Beauty Shop – Online Ordering App (Streamlit)

A simple beauty-products store built with **Streamlit** and **SQLite**.

**Customers can**
- Browse products, filter by category and search by name
- Add products to a cart
- Place an order using **Cash on Delivery (COD)**

**Admin can**
- Log in with a password
- Add, edit and delete products (price, stock, description, image)
- View all orders and change their status (Pending → Confirmed → Shipped → Delivered / Cancelled)

**Offers (set at the top of `app.py`)**
- 🚚 **Free delivery on a customer's first order.** A customer is recognised by their phone number (spaces and dashes are ignored). Cancelled orders don't count. Other orders pay `DELIVERY_FEE` (Rs. 250).
- 🎁 **Free gift on orders of Rs. 10,000 or more** (`GIFT_THRESHOLD`, products only, delivery not counted). The gift (`GIFT_NAME`) is saved on the order so the admin can see what to pack.
- 📦 **25 sample products** in 7 categories. In the Admin panel use **Add sample products** to load any that are missing.

To change an offer, edit the numbers or the gift name near the top of `app.py`:

```python
DELIVERY_FEE = 250
GIFT_THRESHOLD = 10000
GIFT_NAME = "Free Gift: Luxury Beauty Pouch Set"
```

---

## 1. Project files

```
beauty-shop/
├── app.py             # the whole app (UI + database code)
├── requirements.txt   # Python packages the app needs
└── README.md          # this file
```

The database file `beauty_shop.db` is created automatically the first time the app runs, with 6 sample products.

---

## 2. Create the files yourself (step by step)

1. Create a new folder called `beauty-shop` on your computer.
2. Open it in any editor (VS Code, Notepad++, etc.).
3. Create three files with exactly these names: `app.py`, `requirements.txt`, `README.md`.
4. Paste the provided content into each file and save.

---

## 3. Run the app on your computer

You need **Python 3.9 or newer** (check with `python --version`).

```bash
# 1. Go into the project folder
cd beauty-shop

# 2. (Recommended) create a virtual environment
python -m venv venv

# 3. Activate it
#    Windows:
venv\Scripts\activate
#    Mac / Linux:
source venv/bin/activate

# 4. Install the requirements
pip install -r requirements.txt

# 5. Start the app
streamlit run app.py
```

Your browser opens at `http://localhost:8501`.

**Default admin password (local testing only): `admin123`**
Open the **Admin** page from the sidebar and log in with it.

---

## 4. How the code works (read `app.py` top to bottom)

| Step | What it does |
|------|--------------|
| 1. Basic settings | Page title, currency, order statuses, admin password lookup |
| 2. Database helpers | Small functions to create tables and add / read / update / delete products and orders (SQLite) |
| 3. Cart helpers | The cart is a Python dictionary `{product_id: quantity}` kept in `st.session_state` |
| 4. Customer pages | `page_shop()` shows products; `page_cart()` shows the cart and the checkout form |
| 5. Admin pages | `page_admin()` handles login; `admin_products_tab()` and `admin_orders_tab()` manage data |
| 6. Main | The sidebar menu decides which page to show |

Good to know:
- **`st.session_state`** remembers values (like the cart) between button clicks.
- **`st.form`** groups inputs so the app only reruns when the submit button is pressed.
- **`st.rerun()`** refreshes the page after data changes.
- When an order is placed, stock is checked again and reduced, so the same item can't be oversold.
- Each order stores the product name and price at purchase time, so old orders stay correct even if you later edit or delete the product.

---

## 5. Push the project to GitHub

### A. One-time setup
1. Create a free account at <https://github.com>.
2. Install Git from <https://git-scm.com/downloads>.
3. Tell Git who you are (once per computer):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```

### B. Create an empty repository on GitHub
1. On GitHub click **+ → New repository**.
2. Name it, for example, `beauty-shop`.
3. Choose **Public** (Streamlit Community Cloud's free plan works best with public repos; private repos are possible after you grant access).
4. Do **not** tick "Add a README" (you already have one). Click **Create repository**.

### C. Add a `.gitignore` file (recommended)
Create a file named `.gitignore` in your project folder with:

```
venv/
__pycache__/
*.db
.streamlit/secrets.toml
```

This keeps your virtual environment, local database and secrets out of GitHub.

### D. Push your code
Run these in the project folder:

```bash
git init
git add .
git commit -m "Beauty shop app: first version"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/beauty-shop.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. If asked to sign in, use your GitHub login in the browser window that opens, or a Personal Access Token as the password.

To update later after changing code:

```bash
git add .
git commit -m "Describe your change"
git push
```

---

## 6. Deploy on Streamlit Community Cloud (free)

1. Go to <https://share.streamlit.io> and sign in with your **GitHub** account.
2. Click **Create app** (or **New app**) and choose to deploy from an existing repo.
3. Fill in:
   - **Repository:** `YOUR-USERNAME/beauty-shop`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Open **Advanced settings** and paste this into the **Secrets** box (use your own strong password):
   ```toml
   ADMIN_PASSWORD = "choose-a-strong-password"
   ```
5. Click **Deploy**. After a minute or two you get a public link like `https://your-app-name.streamlit.app`.

To change the password later: open your app on share.streamlit.io → **Settings → Secrets**.

Every time you `git push`, the deployed app updates automatically.

---

## 7. Important limitation: data on Streamlit Community Cloud

Streamlit Community Cloud's storage is **temporary**. The SQLite file can be **reset when the app restarts, goes to sleep, or is redeployed**, which would erase products and orders you added through the admin panel.

This is fine for learning and demos. For a real store, switch to an external database (for example Supabase, Neon/PostgreSQL, or Google Sheets) so data is stored permanently.

---

## 8. Ideas to extend the app

- Product image upload
- Order confirmation by email or WhatsApp
- Customer accounts and order history
- Discount codes and delivery charges
- Download orders as a CSV file
- Move to a permanent cloud database

---

## 9. Troubleshooting

| Problem | Fix |
|---------|-----|
| `streamlit: command not found` | Activate your virtual environment, then run `pip install -r requirements.txt` again, or use `python -m streamlit run app.py` |
| Can't log in as admin | Locally use `admin123`; on the cloud use the `ADMIN_PASSWORD` you set in Secrets |
| Deployed app shows an error about a missing module | Make sure `requirements.txt` is in the repo root and lists `streamlit` |
| Products or orders disappeared on the cloud | See section 7 (temporary storage) |
