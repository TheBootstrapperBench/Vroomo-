from flask import Flask, render_template, jsonify, request
import sqlite3
import os

app = Flask(__name__)
DB_PATH = '/tmp/vroomo.db' if os.environ.get('VERCEL') else 'vroomo.db'

def get_db():
    return sqlite3.connect(DB_PATH)

# Initialize SQLite Database
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Cars table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            car_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            location TEXT NOT NULL,
            days_listed INTEGER DEFAULT 0,
            seller_phone TEXT DEFAULT '9876543210'
        )
    ''')

    # Buyer passes table for 169 and 249 plans
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buyer_passes (
            pass_id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER NOT NULL,
            plan_tier INTEGER NOT NULL,
            amount_paid REAL NOT NULL,
            unlocks_remaining INTEGER NOT NULL
        )
    ''')

    # Populate initial sample car
    cursor.execute('SELECT COUNT(*) FROM cars')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO cars (title, price, location, days_listed, seller_phone)
            VALUES ('2020 Maruti Suzuki Swift VXi', 450000, 'Pune', 0, '9876543210')
        ''')

    conn.commit()
    conn.close()

# Initialize DB on start
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/cars/list', methods=['GET'])
def get_cars():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM cars')
    rows = cursor.fetchall()
    cars = [dict(row) for row in rows]
    conn.close()
    
    return jsonify({"status": "success", "total_cars": len(cars), "cars": cars})

@app.route('/api/buyer/buy-pass', methods=['POST'])
def buy_pass():
    data = request.get_json() or {}
    buyer_id = data.get('buyer_id', 1)
    plan_tier = data.get('plan_tier', 169)  # Accepts 169 or 249
    
    # Assign unlocks based on plan
    if plan_tier == 249:
        unlocks = 5
        price = 249.0
    else:
        plan_tier = 169
        unlocks = 3
        price = 169.0

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO buyer_passes (buyer_id, plan_tier, amount_paid, unlocks_remaining)
        VALUES (?, ?, ?, ?)
    ''', (buyer_id, plan_tier, price, unlocks))

    pass_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": f"₹{plan_tier} Pass Activated!",
        "pass_id": pass_id,
        "plan_tier": plan_tier,
        "unlocks_remaining": unlocks
    })

if __name__ == '__main__':
    app.run(debug=True)