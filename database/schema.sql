-- MakFleet Spatio-Temporal Data Warehouse Prototype
-- Database Schema

-- Enable PostGIS extension for spatial data
CREATE EXTENSION IF NOT EXISTS postgis;

-- Drop tables if they exist (in correct order due to foreign keys)
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS telemetry CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS drivers CASCADE;
DROP TABLE IF EXISTS locations CASCADE;

-- Drivers table
CREATE TABLE drivers (
    driver_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    license_number VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vehicles table
CREATE TABLE vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    plate_number VARCHAR(20) UNIQUE NOT NULL,
    driver_id INT REFERENCES drivers(driver_id),
    model VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Telemetry data table (stores raw IoT sensor data)
CREATE TABLE telemetry (
    telemetry_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES vehicles(vehicle_id) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    speed FLOAT NOT NULL,
    acceleration FLOAT,
    engine_temp FLOAT,
    fuel_level FLOAT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Events table (stores detected events from telemetry)
CREATE TABLE events (
    event_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES vehicles(vehicle_id) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    speed FLOAT,
    acceleration FLOAT,
    timestamp TIMESTAMP NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations table (for campus zones)
CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    zone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_telemetry_vehicle_id ON telemetry(vehicle_id);
CREATE INDEX idx_telemetry_timestamp ON telemetry(timestamp);
CREATE INDEX idx_events_vehicle_id ON events(vehicle_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_type ON events(event_type);

-- Create spatial index for PostGIS
CREATE INDEX idx_telemetry_geom ON telemetry USING GIST (ST_MakePoint(longitude, latitude));

-- Insert sample drivers
INSERT INTO drivers (name, phone, license_number) VALUES
    ('John Kato', '+256701234567', 'DL/2020/001'),
    ('Robert Ssali', '+256702345678', 'DL/2020/002'),
    ('David Musoke', '+256703456789', 'DL/2020/003'),
    ('Francis Musinguzi', '+256704567890', 'DL/2020/004'),
    ('Michael Okello', '+256705678901', 'DL/2020/005');

-- Insert sample vehicles
INSERT INTO vehicles (plate_number, driver_id, model, status) VALUES
    ('UBE 001', 1, 'Yamaha NMAX', 'active'),
    ('UBE 002', 2, 'Honda PCX', 'active'),
    ('UBE 003', 3, 'Yamaha Aerox', 'active'),
    ('UBE 004', 4, 'Suzuki Burgman', 'active'),
    ('UBE 005', 5, 'Kymco Like', 'active');

-- Insert sample campus locations
INSERT INTO locations (name, latitude, longitude, zone) VALUES
    ('Main Library', 0.3336, 32.5656, 'Academic'),
    ('Freedom Square', 0.3342, 32.5671, 'Central'),
    ('Engineering Block', 0.3351, 32.5634, 'Academic'),
    ('Mary Stuart Hall', 0.3328, 32.5689, 'Residential'),
    ('Central Teaching Facility', 0.3345, 32.5662, 'Academic'),
    ('Food Court', 0.3339, 32.5685, 'Commercial'),
    ('Sports Complex', 0.3319, 32.5698, 'Recreation'),
    ('Medical School', 0.3362, 32.5645, 'Academic');

-- View to get telemetry with vehicle info
CREATE OR REPLACE VIEW telemetry_with_vehicle AS
SELECT 
    t.telemetry_id,
    t.vehicle_id,
    v.plate_number,
    d.name AS driver_name,
    t.latitude,
    t.longitude,
    t.speed,
    t.acceleration,
    t.engine_temp,
    t.timestamp
FROM telemetry t
JOIN vehicles v ON t.vehicle_id = v.vehicle_id
JOIN drivers d ON v.driver_id = d.driver_id;

-- View to get events with vehicle and driver info
CREATE OR REPLACE VIEW events_with_vehicle AS
SELECT 
    e.event_id,
    e.vehicle_id,
    v.plate_number,
    d.name AS driver_name,
    e.event_type,
    e.latitude,
    e.longitude,
    e.speed,
    e.acceleration,
    e.timestamp,
    e.severity
FROM events e
JOIN vehicles v ON e.vehicle_id = v.vehicle_id
JOIN drivers d ON v.driver_id = d.driver_id;
