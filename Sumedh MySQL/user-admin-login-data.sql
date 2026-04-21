CREATE TABLE IF NOT EXISTS photographers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    phone VARCHAR(20),
    experience TEXT,
    rating FLOAT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    profile_image VARCHAR(500),
    address TEXT
);