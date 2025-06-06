CREATE DATABASE IF NOT EXISTS time_db3;
USE time_db3;

-- Table: categories
CREATE TABLE categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    display_order INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: questions
CREATE TABLE questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    category_id INT NOT NULL,
    question_text VARCHAR(255) NOT NULL,
    display_order INT NOT NULL,
    source_type ENUM('DB', 'STATIC', 'URL') NOT NULL,
    source_detail VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Table: static_answers
CREATE TABLE static_answers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    question_id INT NOT NULL,
    answer_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- Table: url_answers
CREATE TABLE url_answers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    question_id INT NOT NULL,
    subcourse VARCHAR(50),  -- e.g., "CAT26"
    variant VARCHAR(50),    -- e.g., "Online Live Course"
    url VARCHAR(255) NOT NULL,
    answer_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- Table: subcourses
CREATE TABLE subcourses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course VARCHAR(50) NOT NULL,
    subcourse VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: coursetypes
CREATE TABLE coursetypes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course VARCHAR(50) NOT NULL,
    coursetype VARCHAR(50) NOT NULL,
    variant VARCHAR(100),
    usertype VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: coursefee
CREATE TABLE coursefee (
    id INT PRIMARY KEY AUTO_INCREMENT,
    city VARCHAR(50) NOT NULL,
    course VARCHAR(50) NOT NULL,
    subcourse VARCHAR(50) NOT NULL,
    variant VARCHAR(50) NOT NULL,
    actual_lumpsum INT,
    actual_instalments INT,
    discount INT,
    lumpsum INT,
    instalments INT,
    first_instalment INT,
    second_instalment INT,
    third_instalment INT,
    status ENUM('active', 'inactive') DEFAULT 'active',
    mode ENUM('online', 'offline') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: discounts
CREATE TABLE discounts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course VARCHAR(50) NOT NULL,
    subcourse VARCHAR(50) NOT NULL,
    variant VARCHAR(50) NOT NULL,
    discounttype VARCHAR(50) NOT NULL,
    discount_range VARCHAR(20),
    city VARCHAR(50) NOT NULL,
    discount_amount INT,
    test_name VARCHAR(50),
    discount_reason VARCHAR(100),
    discount_start_date DATE,
    discount_end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_details (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    mobile VARCHAR(15) NOT NULL,
    city VARCHAR(50),
    demo_otp VARCHAR(10),  -- Added column for OTP
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE query_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    course VARCHAR(50),
    subcourse VARCHAR(50),
    training_type VARCHAR(50),
    category_id INT,
    question_id INT,
    answer_text TEXT,
    queried_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_details(id)
);

CREATE TABLE url_answer_cache (
    id INT PRIMARY KEY AUTO_INCREMENT,
    question_id INT,
    subcourse VARCHAR(50),
    variant VARCHAR(50),
    url VARCHAR(255),
    answer_text TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: batch_sizes (New)
CREATE TABLE batch_sizes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    city VARCHAR(50) NOT NULL,
    course VARCHAR(50) NOT NULL,
    subcourse VARCHAR(50) NOT NULL,
    variant VARCHAR(50) NOT NULL,
    batch_size INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: exam_info (New)
CREATE TABLE exam_info (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course VARCHAR(50) NOT NULL,
    eligibility_criteria TEXT,
    exam_dates TEXT,
    registration_process TEXT,
    score_validity TEXT,
    top_b_schools TEXT,
    mba_advantages TEXT,
    selection_process TEXT,
    attempts_allowed TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);