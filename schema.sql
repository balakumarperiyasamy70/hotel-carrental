-- Sands Car Rental Database Schema

CREATE TABLE IF NOT EXISTS fleet (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    transmission VARCHAR(20) DEFAULT 'Automatic',
    seats INT DEFAULT 5,
    daily_rate DECIMAL(10,2) NOT NULL,
    plate VARCHAR(20),
    vin VARCHAR(50),
    color VARCHAR(30),
    features VARCHAR(255),
    status ENUM('available','rented','maintenance') DEFAULT 'available',
    icon VARCHAR(10) DEFAULT '🚗',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ref VARCHAR(20) UNIQUE NOT NULL,
    fleet_id INT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    address VARCHAR(255),
    license_no VARCHAR(50) NOT NULL,
    license_state VARCHAR(50) DEFAULT 'Arkansas',
    pickup_location VARCHAR(150),
    dropoff_location VARCHAR(150),
    pickup_date DATE NOT NULL,
    return_date DATE NOT NULL,
    days INT NOT NULL,
    daily_rate DECIMAL(10,2) NOT NULL,
    location_fee DECIMAL(10,2) DEFAULT 15.00,
    insurance_fee DECIMAL(10,2) DEFAULT 0.00,
    total DECIMAL(10,2) NOT NULL,
    deposit DECIMAL(10,2) DEFAULT 200.00,
    notes TEXT,
    status ENUM('pending','approved','declined','active','completed','cancelled') DEFAULT 'pending',
    admin_note TEXT,
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fleet_id) REFERENCES fleet(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed fleet data
INSERT INTO fleet (name, category, year, transmission, seats, daily_rate, plate, color, features, icon) VALUES
('Toyota Corolla',    'Economy',      2023, 'Automatic', 5,  38.00, 'AR-4421', 'White',  'AC,Bluetooth,35 MPG', '🚗'),
('Ford Explorer',     'SUV',          2023, 'Automatic', 7,  72.00, 'AR-8834', 'Silver', 'AC,4WD,Sunroof,Nav',  '🚙'),
('BMW 5 Series',      'Luxury',       2023, 'Automatic', 5, 120.00, 'AR-2290', 'Black',  'AC,Leather,Nav,Premium Audio', '🏎️'),
('Ford F-150',        'Pickup Truck', 2022, 'Automatic', 5,  85.00, 'AR-5517', 'Red',    'AC,4WD,Tow Hitch,Bed Liner',   '🛻'),
('Mercedes Sprinter', 'Van',          2022, 'Manual',   12,  95.00, 'AR-3310', 'White',  'AC,Cargo Space',      '🚐'),
('Tesla Model 3',     'Electric',     2024, 'Automatic', 5, 110.00, 'AR-7799', 'Blue',   'Autopilot,350mi Range,Premium', '⚡');

-- Seed admin user (password: ########!)
INSERT INTO admin_users (username, password_hash, name) VALUES
('admin', 'pbkdf2:sha256:600000$placeholder$placeholder', 'Admin');
