# database.py
import sqlite3
from datetime import datetime

def init_db():
 conn = sqlite3.connect('/app/storage/ecommerce.db') # مسار وحدة التخزين في Railway
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

# وظائف إدارة الأقسام
def add_category(name):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 c.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
 conn.commit()
 conn.close()

def get_categories():
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 c.execute("SELECT * FROM categories")
 categories = c.fetchall()
 conn.close()
 return categories

# وظائف إدارة المنتجات
def add_product(name, description, price, image, category_id, stock=10):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 c.execute("INSERT INTO products (name, description, price, image, category_id, stock) VALUES (?, ?, ?, ?, ?, ?)",
 (name, description, price, image, category_id, stock))
 conn.commit()
 conn.close()

def get_products(category_id=None):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 if category_id:
 c.execute("SELECT * FROM products WHERE category_id = ?", (category_id,))
 else:
 c.execute("SELECT * FROM products")
 products = c.fetchall()
 conn.close()
 return products

def delete_product(product_id):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 c.execute("DELETE FROM products WHERE id = ?", (product_id,))
 conn.commit()
 conn.close()

def update_product(product_id, name=None, description=None, price=None, image=None, category_id=None, stock=None):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
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

# وظائف إدارة الطلبيات
def add_order(customer_id, customer_name, phone, state, municipality, address, delivery_type, total_price):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
 c.execute("INSERT INTO orders (customer_id, customer_name, phone, state, municipality, address, delivery_type, total_price, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
 (customer_id, customer_name, phone, state, municipality, address, delivery_type, total_price, "new", created_at))
 order_id = c.lastrowid
 conn.commit()
 conn.close()
 return order_id

def add_order_item(order_id, product_id, quantity):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
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

def get_orders(status=None):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 if status:
 c.execute("SELECT * FROM orders WHERE status = ?", (status,))
 else:
 c.execute("SELECT * FROM orders")
 orders = c.fetchall()
 conn.close()
 return orders

def update_order_status(order_id, status):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 c.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
 conn.commit()
 conn.close()

# وظائف إدارة أسعار التوصيل
def set_delivery_fee(state, office_fee, home_fee):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 c.execute("INSERT OR REPLACE INTO delivery_fees (state, office_fee, home_fee) VALUES (?, ?, ?)",
 (state, office_fee, home_fee))
 conn.commit()
 conn.close()

def get_delivery_fee(state, delivery_type):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 c.execute("SELECT office_fee, home_fee FROM delivery_fees WHERE state = ?", (state,))
 result = c.fetchone()
 conn.close()
 if result:
 return result[0] if delivery_type == "office" else result[1]
 return 0

# وظائف إدارة معلومات الاتصال
def set_contact_info(type, value, display_name):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 c.execute("INSERT OR REPLACE INTO contact_info (type, value, display_name) VALUES (?, ?, ?)",
 (type, value, display_name))
 conn.commit()
 conn.close()

def get_contact_info():
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 c.execute("SELECT * FROM contact_info")
 contacts = c.fetchall()
 conn.close()
 return contacts

# وظائف إدارة الاقتراحات
def add_suggestion(customer_id, text):
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
 c.execute("INSERT INTO suggestions (customer_id, text, created_at) VALUES (?, ?, ?)",
 (customer_id, text, created_at))
 conn.commit()
 conn.close()

def get_suggestions():
 conn = sqlite3.connect('/app/storage/ecommerce.db')
 c = conn.cursor()
 c.execute("SELECT * FROM suggestions")
 suggestions = c.fetchall()
 conn.close()
 return suggestions

if __name__ == "__main__":
 init_db()
