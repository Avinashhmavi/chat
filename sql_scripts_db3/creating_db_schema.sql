-- Add tables to the existing remote MySQL database (db1)
use timeonli_sample;
-- Table: categories
CREATE TABLE IF NOT EXISTS categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    display_order INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: questions
CREATE TABLE IF NOT EXISTS questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    category_id INT NOT NULL,
    question_text VARCHAR(255) NOT NULL,
    display_order INT NOT NULL,
    source_type ENUM('DB', 'STATIC') NOT NULL,
    source_detail VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Table: static_answers
CREATE TABLE IF NOT EXISTS static_answers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    question_id INT NOT NULL,
    answer_text TEXT CHARACTER SET utf8mb4 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id)
) CHARACTER SET utf8mb4;

-- Table: subcourses
CREATE TABLE IF NOT EXISTS subcourses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course VARCHAR(50) NOT NULL,
    subcourse VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: user_details
CREATE TABLE IF NOT EXISTS user_details (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    mobile VARCHAR(15) NOT NULL,
    city VARCHAR(50),
    demo_otp VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: query_history
CREATE TABLE IF NOT EXISTS query_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    course VARCHAR(50),
    subcourse VARCHAR(50),
    training_type VARCHAR(100),
    category_id INT,
    question_id INT,
    answer_text TEXT CHARACTER SET utf8mb4,
    queried_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_details(id)
) CHARACTER SET utf8mb4;

-- Table: exam_info
CREATE TABLE IF NOT EXISTS exam_info (
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