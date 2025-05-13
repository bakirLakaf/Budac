import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('ecommerce.db')
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
    print("Created ecommerce.db successfully!")

if __name__ == "__main__":
    init_db()