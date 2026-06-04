-- Create Database (run separately if needed)
-- CREATE DATABASE number_plate;

-- -------------------------------
-- USERS TABLE
-- -------------------------------
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    address TEXT NOT NULL,
    mobile_no VARCHAR(15) NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- -------------------------------
-- VEHICLE REGISTRATION TABLE
-- -------------------------------
CREATE TABLE vehicle_registration (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    vehicle_number VARCHAR(20) UNIQUE NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    status VARCHAR(10) DEFAULT 'Paid',
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);