-- Initialize database with sample data
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    stock INTEGER NOT NULL,
    rating NUMERIC(3,1) NOT NULL,
    description TEXT
);

-- Insert sample data
INSERT INTO products (name, category, price, stock, rating, description) VALUES
('Wireless Noise-Cancelling Headphones', 'Electronics', 149.99, 35, 4.7, 'Over-ear headphones with active noise cancellation'),
('Ergonomic Office Chair', 'Furniture', 329.00, 12, 4.5, 'Lumbar-support mesh chair adjustable for all-day comfort'),
('Stainless Steel Water Bottle', 'Home', 24.95, 120, 4.8, 'Double-walled 32 oz bottle keeps drinks cold 24 h or hot 12 h'),
('4K Webcam Pro', 'Electronics', 99.99, 30, 4.4, '1080p/4K autofocus webcam with built-in ring light'),
('Mechanical Keyboard', 'Electronics', 89.99, 60, 4.6, 'Compact TKL layout with Cherry MX Brown switches'),
('Cast Iron Skillet 12"', 'Kitchen', 39.95, 70, 4.9, 'Pre-seasoned; compatible with all cooktops including induction'),
('French Press Coffee Maker', 'Kitchen', 34.99, 65, 4.7, '8-cup borosilicate glass carafe with stainless double-screen filter'),
('Electric Kettle 1.7L', 'Kitchen', 44.99, 60, 4.7, '1500W rapid boil, 6 temperature presets, keep-warm function'),
('Resistance Bands Set', 'Sports', 19.99, 150, 4.5, '5 resistance levels, latex-free, includes carry bag'),
('Foam Roller Deep Tissue', 'Sports', 29.99, 100, 4.3, 'High-density EVA foam; 36-inch length for full-back coverage'),
('Yoga Mat Premium', 'Sports', 45.00, 80, 4.4, '6mm thick non-slip mat with alignment lines; eco-friendly TPE foam'),
('Running Shoes Pro', 'Sports', 119.99, 55, 4.6, 'Lightweight breathable mesh upper with responsive foam midsole'),
('Bamboo Cutting Board Set', 'Kitchen', 32.00, 85, 4.6, '3-piece set with juice groove; naturally antimicrobial bamboo'),
('Monitor Light Bar', 'Electronics', 35.99, 75, 4.5, 'Clip-on LED bar with auto-dimming sensor'),
('Smart LED Desk Lamp', 'Electronics', 49.99, 90, 4.5, 'Touch-control, 5 colour temperatures, USB-C charging'),
('Portable Bluetooth Speaker', 'Electronics', 59.99, 45, 4.5, 'IPX7 waterproof, 360 sound, 12-hour playback'),
('Standing Desk Converter', 'Furniture', 249.00, 18, 4.2, 'Sit-stand desktop riser with smooth gas-spring lift mechanism'),
('Air Purifier HEPA', 'Home', 199.00, 25, 4.3, 'Covers up to 500 sq ft; removes 99.97% of particles'),
('Smart Thermostat', 'Home', 44.95, 40, 4.4, 'WiFi-enabled with learning algorithm and energy saving'),
('Non-Stick Cookware Set', 'Kitchen', 45.00, 50, 4.5, '10-piece set with ceramic coating and stay-cool handles');
