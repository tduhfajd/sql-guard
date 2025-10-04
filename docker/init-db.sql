-- Initialize SQL-Guard production database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table for demo data
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert demo data
INSERT INTO users (email, name, phone) VALUES 
    ('admin@demo.com', 'Admin User', '+1234567890'),
    ('operator@demo.com', 'Operator User', '+1234567891'),
    ('viewer@demo.com', 'Viewer User', '+1234567892')
ON CONFLICT (email) DO NOTHING;

-- Create orders table for demo data
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending',
    amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert demo orders
INSERT INTO orders (user_id, status, amount) VALUES 
    (1, 'pending', 100.00),
    (2, 'paid', 250.50),
    (3, 'cancelled', 75.25)
ON CONFLICT DO NOTHING;
