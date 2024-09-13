-- Create the database if it doesn't exist
CREATE DATABASE your_database_name;

-- Connect to the new database
\c your_database_name

-- Create a new user if it doesn't exist
CREATE USER evachatuser WITH PASSWORD 'your_password_here';

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE your_database_name TO evachatuser;
GRANT ALL PRIVILEGES ON SCHEMA public TO evachatuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO evachatuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO evachatuser;

-- Alter default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO evachatuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO evachatuser;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    sender UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(20) NOT NULL,
    FOREIGN KEY (sender) REFERENCES users(id) ON DELETE SET NULL
);