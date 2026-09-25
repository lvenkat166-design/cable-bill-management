import sqlite3

DATABASE = "cable_bills.db"


def get_connection():
    return sqlite3.connect(DATABASE)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            monthly_bill REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            year INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            payment_date TEXT,
            FOREIGN KEY (customer_id)
            REFERENCES customers(customer_id)
        )
    """)

    conn.commit()
    conn.close()