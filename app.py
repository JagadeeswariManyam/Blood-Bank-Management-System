from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = "change_this_secret_key_to_a_random_value"  # change before deployment

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='bloodbank'
    )

# Simple validation helpers
def valid_blood_group(bg):
    return bg in ['A+','A-','B+','B-','O+','O-','AB+','AB-']

def valid_positive_int(val):
    try:
        v = int(val)
        return v > 0
    except Exception:
        return False

# Home
@app.route('/')
def home():
    return render_template('index.html')

# Admin login (simple)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

        # check password - try werkzeug check_password_hash if available, else compare sha256
        try:
            from werkzeug.security import check_password_hash
            ok = check_password_hash(user['password_hash'], password)
        except Exception:
            import hashlib
            ok = hashlib.sha256(password.encode()).hexdigest() == user['password_hash']

        if ok:
            session['admin'] = username
            flash('Logged in successfully', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logged out', 'info')
    return redirect(url_for('home'))

# Add donor
@app.route('/add_donor', methods=['GET', 'POST'])
def add_donor():
    if request.method == 'POST':
        name = request.form['name'].strip()
        blood_group = request.form['blood_group'].strip()
        contact = request.form['contact'].strip()
        last_donation = request.form.get('last_donation') or None

        if not name or not valid_blood_group(blood_group):
            flash('Please provide valid donor name and blood group.', 'danger')
            return redirect(url_for('add_donor'))

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""INSERT INTO donors (name, blood_group, contact, last_donation)
                              VALUES (%s, %s, %s, %s)""", (name, blood_group, contact, last_donation))
            # update inventory
            cursor.execute("""INSERT INTO inventory (blood_group, units) VALUES (%s, 1)
                              ON DUPLICATE KEY UPDATE units = units + 1""", (blood_group,))
            conn.commit()
            flash('Donor added and inventory updated', 'success')
        except Exception as e:
            conn.rollback()
            flash('Error adding donor: ' + str(e), 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('add_donor'))

    return render_template('add_donor.html')

# View donors
@app.route('/donors_list')
def donors_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM donors ORDER BY donor_id DESC")
    donors = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('donors_list.html', donors=donors)

# Inventory
@app.route('/inventory')
def inventory():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM inventory ORDER BY blood_group")
    inventory = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('inventory.html', inventory=inventory)

# Request blood
@app.route('/request_blood', methods=['GET', 'POST'])
def request_blood():
    if request.method == 'POST':
        hospital_name = request.form['hospital_name'].strip()
        patient_name = request.form['patient_name'].strip()
        blood_group = request.form['blood_group'].strip()
        units_required = request.form['units_required'].strip()

        if not hospital_name or not patient_name or not valid_blood_group(blood_group) or not valid_positive_int(units_required):
            flash('Please provide valid request details.', 'danger')
            return redirect(url_for('request_blood'))

        units_required = int(units_required)
        request_date = datetime.now().strftime('%Y-%m-%d')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT units FROM inventory WHERE blood_group = %s", (blood_group,))
            result = cursor.fetchone()
            if result and result['units'] >= units_required:
                new_units = result['units'] - units_required
                cursor.execute("UPDATE inventory SET units = %s WHERE blood_group = %s", (new_units, blood_group))
                status = 'Approved'
                flash(f'Request approved: {units_required} units of {blood_group}', 'success')
            else:
                status = 'Pending'
                flash('Not enough units. Request marked as pending.', 'warning')

            cursor.execute("""INSERT INTO requests (hospital_name, patient_name, blood_group, units_required, request_date, status)
                              VALUES (%s, %s, %s, %s, %s, %s)""", (hospital_name, patient_name, blood_group, units_required, request_date, status))
            conn.commit()
        except Exception as e:
            conn.rollback()
            flash('Error processing request: ' + str(e), 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('request_blood'))

    return render_template('request_blood.html')

# View requests (admin can approve pending)
@app.route('/view_requests', methods=['GET', 'POST'])
def view_requests():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        if 'admin' not in session:
            flash('Admin login required to approve requests.', 'danger')
            return redirect(url_for('login'))
        req_id = request.form.get('approve_id')
        if not req_id or not req_id.isdigit():
            flash('Invalid request id', 'danger')
            return redirect(url_for('view_requests'))

        try:
            cursor.execute("SELECT * FROM requests WHERE request_id = %s", (req_id,))
            r = cursor.fetchone()
            if not r:
                flash('Request not found', 'danger')
            else:
                # check inventory again before approving
                cursor.execute("SELECT units FROM inventory WHERE blood_group = %s", (r['blood_group'],))
                inv = cursor.fetchone()
                if inv and inv['units'] >= r['units_required']:
                    new_units = inv['units'] - r['units_required']
                    cursor.execute("UPDATE inventory SET units = %s WHERE blood_group = %s", (new_units, r['blood_group']))
                    cursor.execute("UPDATE requests SET status = 'Approved' WHERE request_id = %s", (req_id,))
                    conn.commit()
                    flash('Request approved and inventory updated', 'success')
                else:
                    flash('Not enough inventory to approve', 'danger')
        except Exception as e:
            conn.rollback()
            flash('Error during approval: ' + str(e), 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('view_requests'))

    cursor.execute("SELECT * FROM requests ORDER BY request_date DESC")
    requests_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_requests.html', requests=requests_list)

if __name__ == '__main__':
    app.run(debug=True)
