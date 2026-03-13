<<<<<<< HEAD
Blood Bank Management System
===========================

What's included
- Flask app (app.py)
- Templates using Bootstrap (templates/)
- SQL schema (bloodbank_schema.sql) to create database & initial data
- Basic admin login (username: admin, password: admin123)
- Security notes: prepared statements, input validation, session-based admin authentication.
  Passwords are stored as hashes. Hash method used when generating this package: werkzeug_generate_password_hash (PBKDF2)

Setup instructions
1. Install Python 3.8+ and pip.
2. Create a virtualenv (recommended) and activate it.
3. Install requirements:
   pip install -r requirements.txt
4. Import the SQL schema into your local MySQL server:
   - mysql -u root -p < bloodbank_schema.sql
5. Edit app.py if your MySQL credentials are different.
6. Run the app:
   python app.py
7. Open http://127.0.0.1:5000 in your browser.

Change default admin password
- Login as admin (admin/admin123) and then update the users table to change the password hash.
- For production, replace the default secret key in app.py with a secure random value.

Notes & security recommendations
- This project uses prepared statements and basic validation.
- For production use:
  - Use TLS (HTTPS)
  - Use salted hashing algorithms (bcrypt/argon2). The package tries to use Werkzeug's PBKDF2 if available.
  - Do not ship with default admin credentials.
  - Limit access to the database and use environment variables for secrets.
=======
# Blood-bank-management-system
>>>>>>> ee8e9460308ca1a25367d1fb03dc17b286950121
