import sqlite3
from datetime import datetime
import os
import git
import shutil

# مسار قاعدة البيانات
DB_PATH = '/app/storage/ecommerce.db' if os.getenv('RAILWAY_ENVIRONMENT') else 'ecommerce.db'
# مسار الملف في المستودع
REPO_DB_PATH = 'storage/ecommerce.db'
# رابط المستودع (استبدله برابطك)
REPO_URL = 'https://github.com/bakirLakaf/budac.git'  # مثل https://github.com/USERNAME/Budac.git
# إذا كان المستودع خاص، استخدم رمز وصول
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if GITHUB_TOKEN:
    REPO_URL = f'https://{GITHUB_TOKEN}@github.com/bakirLakaf/budac.git'
# مجلد مؤقت للمستودع
REPO_DIR = '/tmp/repo' if os.getenv('RAILWAY_ENVIRONMENT') else 'tmp_repo'

def init_git_repo():
    """تهيئة المستودع وسحب قاعدة البيانات"""
    if not os.path.exists(REPO_DIR):
        os.makedirs(REPO_DIR, exist_ok=True)
        repo = git.Repo.clone_from(REPO_URL, REPO_DIR)
    else:
        repo = git.Repo(REPO_DIR)
        repo.remotes.origin.pull()
    # نسخ قاعدة البيانات للمسار المحلي
    src_db = os.path.join(REPO_DIR, REPO_DB_PATH)
    if os.path.exists(src_db):
        shutil.copy(src_db, DB_PATH)
    return repo

def commit_and_push(repo):
    """رفع التغييرات لقاعدة البيانات"""
    shutil.copy(DB_PATH, os.path.join(REPO_DIR, REPO_DB_PATH))
    repo.index.add([REPO_DB_PATH])
    repo.index.commit(f"Update ecommerce.db at {datetime.now()}")
    repo.remotes.origin.push()

def init_db():
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # جدول الأقسام
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')

    # جدول المنتجات
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT,
                  price REAL, image TEXT, category_id INTEGER, stock INTEGER,
                  FOREIGN KEY(category_id) REFERENCES categories(id))''')

    # جدول الطلبيات
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, customer_name TEXT,
                  phone TEXT, state TEXT, municipality TEXT, address TEXT, delivery_type TEXT,
                  total_price REAL, status TEXT, created_at TEXT)''')

    # جدول عناصر الطلبية
    c.execute('''CREATE TABLE IF NOT EXISTS order_items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, product_id INTEGER,
                  quantity INTEGER, FOREIGN KEY(order_id) REFERENCES orders(id),
                  FOREIGN KEY(product_id) REFERENCES products(id))''')

    # جدول أسعار التوصيل
    c.execute('''CREATE TABLE IF NOT EXISTS delivery_fees
                 (state TEXT PRIMARY KEY, office_fee REAL, home_fee REAL)''')

    # جدول معلومات الاتصال
    c.execute('''CREATE TABLE IF NOT EXISTS contact_info
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, value TEXT, display_name TEXT)''')

    # جدول الاقتراحات
    c.execute('''CREATE TABLE IF NOT EXISTS suggestions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, text TEXT,
                  created_at TEXT)''')

    # إضافة معلومات الاتصال الافتراضية
    c.execute("INSERT OR IGNORE INTO contact_info (type, value, display_name) VALUES (?, ?, ?)",
              ("facebook", "https://www.facebook.com/profile.php?id=100065654981659", "صفحتنا على فيسبوك"))
    c.execute("INSERT OR IGNORE INTO contact_info (type, value, display_name) VALUES (?, ?, ?)",
              ("phone", "0676672334", "اتصل بنا - الرقم الأول"))
    c.execute("INSERT OR IGNORE INTO contact_info (type, value, display_name) VALUES (?, ?, ?)",
              ("whatsapp", "https://wa.me/213676672334", "واتساب - الرقم الأول"))
    c.execute("INSERT OR IGNORE INTO contact_info (type, value, display_name) VALUES (?, ?, ?)",
              ("phone", "0557253033", "اتصل بنا - الرقم الثاني"))
    c.execute("INSERT OR IGNORE INTO contact_info (type, value, display_name) VALUES (?, ?, ?)",
              ("whatsapp", "https://wa.me/213557253033", "واتساب - الرقم الثاني"))

    conn.commit()
    conn.close()
    commit_and_push(repo)

# وظائف إدارة الأقسام
def add_category(name):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    commit_and_push(repo)

def get_categories():
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM categories")
    categories = c.fetchall()
    conn.close()
    return categories

# وظائف إدارة المنتجات
def add_product(name, description, price, image, category_id, stock=10):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO products (name, description, price, image, category_id, stock) VALUES (?, ?, ?, ?, ?, ?)",
              (name, description, price, image, category_id, stock))
    conn.commit()
    conn.close()
    commit_and_push(repo)

def get_products(category_id=None):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if category_id:
        c.execute("SELECT * FROM products WHERE category_id = ?", (category_id,))
    else:
        c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return products

def delete_product(product_id):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    commit_and_push(repo)

def update_product(product_id, name=None, description=None, price=None, image=None, category_id=None, stock=None):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    updates = []
    values = []
    if name:
        updates.append("name = ?")
        values.append(name)
    if description:
        updates.append("description = ?")
        values.append(description)
    if price is not None:
        updates.append("price = ?")
        values.append(price)
    if image:
        updates.append("image = ?")
        values.append(image)
    if category_id:
        updates.append("category_id = ?")
        values.append(category_id)
    if stock is not None:
        updates.append("stock = ?")
        values.append(stock)
    if updates:
        values.append(product_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
        c.execute(query, values)
    conn.commit()
    conn.close()
    commit_and_push(repo)

# وظائف إدارة الطلبيات
def add_order(customer_id, customer_name, phone, state, municipality, address, delivery_type, total_price):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO orders (customer_id, customer_name, phone, state, municipality, address, delivery_type, total_price, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (customer_id, customer_name, phone, state, municipality, address, delivery_type, total_price, "new", created_at))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    commit_and_push(repo)
    return order_id

def add_order_item(order_id, product_id, quantity):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    stock = c.fetchone()[0]
    if stock < quantity:
        conn.close()
        raise ValueError("الكمية المطلوبة غير متوفرة في المخزون!")
    c.execute("INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
              (order_id, product_id, quantity))
    c.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
    conn.commit()
    conn.close()
    commit_and_push(repo)

def get_orders(status=None):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if status:
        c.execute("SELECT * FROM orders WHERE status = ?", (status,))
    else:
        c.execute("SELECT * FROM orders")
    orders = c.fetchall()
    conn.close()
    return orders

def update_order_status(order_id, status):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()
    commit_and_push(repo)

# وظائف إدارة أسعار التوصيل
def set_delivery_fee(state, office_fee, home_fee):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO delivery_fees (state, office_fee, home_fee) VALUES (?, ?, ?)",
              (state, office_fee, home_fee))
    conn.commit()
    conn.close()
    commit_and_push(repo)

def get_delivery_fee(state, delivery_type):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT office_fee, home_fee FROM delivery_fees WHERE state = ?", (state,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0] if delivery_type == "office" else result[1]
    return 0

# وظائف إدارة معلومات الاتصال
def set_contact_info(type, value, display_name):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO contact_info (type, value, display_name) VALUES (?, ?, ?)",
              (type, value, display_name))
    conn.commit()
    conn.close()
    commit_and_push(repo)

def get_contact_info():
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM contact_info")
    contacts = c.fetchall()
    conn.close()
    return contacts

# وظائف إدارة الاقتراحات
def add_suggestion(customer_id, text):
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO suggestions (customer_id, text, created_at) VALUES (?, ?, ?)",
              (customer_id, text, created_at))
    conn.commit()
    conn.close()
    commit_and_push(repo)

def get_suggestions():
    repo = init_git_repo()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM suggestions")
    suggestions = c.fetchall()
    conn.close()
    return suggestions

if __name__ == "__main__":
    init_db()