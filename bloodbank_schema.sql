-- Blood Bank schema (final)
CREATE DATABASE IF NOT EXISTS bloodbank;
USE bloodbank;

CREATE TABLE IF NOT EXISTS donors (
    donor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    blood_group VARCHAR(5) NOT NULL,
    contact VARCHAR(15),
    last_donation DATE
);

CREATE TABLE IF NOT EXISTS inventory (
    blood_group VARCHAR(5) PRIMARY KEY,
    units INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_name VARCHAR(100) NOT NULL,
    patient_name VARCHAR(100) NOT NULL,
    blood_group VARCHAR(5) NOT NULL,
    units_required INT NOT NULL,
    request_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL
);

-- Users table for admin (store password hashes)
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

-- Insert initial inventory
INSERT INTO inventory (blood_group, units) VALUES
('A+', 10),('A-', 5),('B+', 8),('B-', 4),('O+', 12),('O-', 6),('AB+', 3),('AB-', 2)
ON DUPLICATE KEY UPDATE units=VALUES(units);

-- Insert default admin (username: admin, password: admin123)
INSERT INTO users (username, password_hash) VALUES ('admin', 'scrypt:32768:8:1$b46eYJoVBkuJ2yft$4c1218cc7ec6e7462cf830d7200f04062025f1e12b0ec74c69097b74b37fc819ac4b28b49278aac17ea9995fdfa839ede2a53339dde8d42f3537abec84ffc2e4')
ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash);
