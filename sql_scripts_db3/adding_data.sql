USE time_db3;

-- Insert categories
INSERT INTO categories (name, display_order) VALUES
    ('Fees, Discounts & Scholarships', 1),
    ('Courses & Batches', 2),
    ('Study Material & Mock Tests', 3),
    ('Results & Support', 4),
    ('Extra questions', 5),
    ('Contact & Facilities', 6),
    ('App / Online Portal', 7),
    ('Exam & Other Info', 8);

-- Insert questions
INSERT INTO questions (category_id, question_text, display_order, source_type, source_detail) VALUES
    -- Fees, Discounts & Scholarships
    (1, 'What is the course fee?', 1, 'DB', 'coursefee'),
    (1, 'Is there an installment option?', 2, 'DB', 'coursefee'),
    (1, 'Are there any discounts?', 3, 'DB', 'discounts'),
    (1, 'Is there a scholarship test?', 4, 'DB', 'discounts'),
    (1, 'Referral discounts available?', 5, 'STATIC', NULL),
    -- Courses & Batches
    (2, 'What are the batch timings?', 1, 'URL', NULL),
    (2, 'What is the duration of the course and Validity?', 2, 'URL', NULL),
    (2, 'What’s the batch size?', 3, 'DB', 'batch_sizes'),
    (2, 'When is the next batch starting?', 4, 'URL', NULL),
    (2, 'Is it a weekday / weekend - How many days a week?', 5, 'URL', NULL),
    (2, 'Are demo classes available?', 6, 'STATIC', NULL),
    -- Study Material & Mock Tests
    (3, 'What material is provided?', 1, 'URL', NULL),
    (3, 'Number of mock tests?', 2, 'URL', NULL),
    (3, 'Are mocks aligned with the actual exam?', 3, 'URL', NULL),
    (3, 'Access to online tests?', 4, 'URL', NULL),
    (3, 'Mock analysis and solutions?', 5, 'URL', NULL),
    (3, 'Number of books provided?', 6, 'URL', NULL),
    (3, 'Are Mocks all India based?', 7, 'URL', NULL),
    (3, 'How many mocks are Self administered?', 8, 'URL', NULL),
    (3, 'Do you train for other management entrance exams?', 9, 'URL', NULL),
    (3, 'Do you have video sessions?', 10, 'URL', NULL),
    -- Results & Support
    (4, 'Previous results / student performance?', 1, 'URL', NULL),
    (4, 'Testimonials or success stories?', 2, 'DB', 'testimonials'),
    (4, 'Doubt Clarifications?', 3, 'STATIC', NULL),
    (4, 'Mentoring Session on B-school selection?', 4, 'STATIC', NULL),
    (4, 'Application assistance for B-schools/universities?', 5, 'URL', NULL),
    (4, 'SOP/Profile building services?', 6, 'STATIC', NULL),
    -- Extra questions
    (5, 'What will happen if I miss a class?', 1, 'STATIC', NULL),
    (5, 'Do you conduct special classes?', 2, 'STATIC', NULL),
    (5, 'Do you have individual mentorship?', 3, 'STATIC', NULL),
    -- Contact & Facilities
    (6, 'Nearest branch location?', 1, 'DB', 'mdl_location_centerdetails'),
    (6, 'A/c Classrooms, Library, Lab facility?', 2, 'STATIC', NULL),
    (6, 'Contact details?', 3, 'DB', 'mdl_location_centerdetails'),
    (6, 'Accommodation/hostel tie-ups?', 4, 'STATIC', NULL),
    (6, 'Center amenities (Wi-Fi etc.)?', 5, 'STATIC', NULL),
    -- App / Online Portal
    (7, 'Do you have an app or portal / WhatsApp / Telegram support?', 1, 'STATIC', NULL),
    (7, 'What are its features?', 2, 'DB', 'tbd_app_features'),
    (7, 'Access to live & recorded sessions?', 3, 'STATIC', NULL),
    -- Exam & Other Info
    (8, 'What are the eligibility criteria?', 1, 'DB', 'eligibility_criteria'),
    (8, 'When are the exam dates?', 2, 'DB', 'exam_dates'),
    (8, 'How to register for the exam?', 3, 'DB', 'registration_process'),
    (8, 'What is the score validity?', 4, 'DB', 'score_validity'),
    (8, 'List of Top B-schools?', 5, 'DB', 'top_b_schools'),
    (8, 'Advantages of MBA?', 6, 'DB', 'mba_advantages'),
    (8, 'B-school selection process?', 7, 'DB', 'selection_process'),
    (8, 'How many attempts are allowed?', 8, 'DB', 'attempts_allowed');

-- Insert static answers
INSERT INTO static_answers (question_id, answer_text) VALUES
    ((SELECT id FROM questions WHERE question_text = 'Referral discounts available?'), 'Please reach us further details at 040 - 40088300/401'),
    ((SELECT id FROM questions WHERE question_text = 'Are demo classes available?'), 'Yes'),
    ((SELECT id FROM questions WHERE question_text = 'Doubt Clarifications?'), 'Doubt Clarification through email/chat/telegram groups'),
    ((SELECT id FROM questions WHERE question_text = 'Mentoring Session on B-school selection?'), 'Yes mentoring sessions will be conducted for B-school selection'),
    ((SELECT id FROM questions WHERE question_text = 'SOP/Profile building services?'), 'Yes will be provided as part of the GWPI module'),
    ((SELECT id FROM questions WHERE question_text = 'What will happen if I miss a class?'), 'You can take back-up class when conducted for other batch'),
    ((SELECT id FROM questions WHERE question_text = 'Do you conduct special classes?'), 'Special workshops will be conducted on different topics'),
    ((SELECT id FROM questions WHERE question_text = 'Do you have individual mentorship?'), 'We provide mentorship as per the requirement'),
    ((SELECT id FROM questions WHERE question_text = 'A/c Classrooms, Library, Lab facility?'), 'We have library facility available. Lab facility available to take invigilated Mock Tests'),
    ((SELECT id FROM questions WHERE question_text = 'Accommodation/hostel tie-ups?'), 'No, we don\'t have hostel facility or we have tie-up with Hostels'),
    ((SELECT id FROM questions WHERE question_text = 'Center amenities (Wi-Fi etc.)?'), 'Wi-Fi or internet facility is not available'),
    ((SELECT id FROM questions WHERE question_text = 'Do you have an app or portal / WhatsApp / Telegram support?'), 'Yes we have telegram channel support: TIME4CAT\nTIME4CAT is our app and www.time4education.com is our website'),
    ((SELECT id FROM questions WHERE question_text = 'Access to live & recorded sessions?'), 'Yes');

-- Insert URL answers
INSERT INTO url_answers (question_id, subcourse, variant, url, answer_text) VALUES
    ((SELECT id FROM questions WHERE question_text = 'What are the batch timings?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', 'Batches start every Monday at 10 AM.'),
    ((SELECT id FROM questions WHERE question_text = 'What is the duration of the course and Validity?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', 'Course duration is 6 months, valid for 1 year.'),
    ((SELECT id FROM questions WHERE question_text = 'When is the next batch starting?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', 'Next batch starts on the first Monday of next month.'),
    ((SELECT id FROM questions WHERE question_text = 'Is it a weekday / weekend - How many days a week?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', 'Weekend batches, 2 days a week.'),
    ((SELECT id FROM questions WHERE question_text = 'What material is provided?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', 'Comprehensive study material including books and online resources.'),
    ((SELECT id FROM questions WHERE question_text = 'Number of mock tests?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', '20 mock tests provided.'),
    ((SELECT id FROM questions WHERE question_text = 'Are mocks aligned with the actual exam?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', 'Yes, mocks are designed to mirror the actual exam.'),
    ((SELECT id FROM questions WHERE question_text = 'Access to online tests?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', 'Yes, full access to online test portal.'),
    ((SELECT id FROM questions WHERE question_text = 'Mock analysis and solutions?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', 'Detailed analysis and solutions provided.'),
    ((SELECT id FROM questions WHERE question_text = 'Number of books provided?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', '5 books provided.'),
    ((SELECT id FROM questions WHERE question_text = 'Are Mocks all India based?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', 'Yes, mocks are all-India based.'),
    ((SELECT id FROM questions WHERE question_text = 'How many mocks are Self administered?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', '10 self-administered mocks.'),
    ((SELECT id FROM questions WHERE question_text = 'Do you train for other management entrance exams?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', 'Yes, training for GMAT, CMAT, and others.'),
    ((SELECT id FROM questions WHERE question_text = 'Do you have video sessions?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/newtheme/course-details.php?course=9&tid=203', 'Yes, video sessions available.'),
    ((SELECT id FROM questions WHERE question_text = 'Previous results / student performance?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/', 'Over 90% success rate in past exams.'),
    ((SELECT id FROM questions WHERE question_text = 'Application assistance for B-schools/universities?'), 'CAT26', 'Online Live Course', 'https://www.time4education.com/CAT-MBA/Choosing-the-right-B-school', 'Application assistance provided.');

-- Insert subcourses
INSERT INTO subcourses (course, subcourse) VALUES
    ('CAT', 'CAT25'),
    ('CAT', 'CAT26'),
    ('CAT', 'CAT27');

-- Insert coursetypes
INSERT INTO coursetypes (course, coursetype, variant, usertype) VALUES
    ('CAT26', 'Classroom Course', 'Long Term, Super Long Term', 'CAT26'),
    ('CAT26', 'Online Live Course', 'onlinelive', 'CAT26'),
    ('CAT26', 'Online recorded Course', 'online', 'CAT26'),
    ('CAT26', 'Correspondence', 'regular, advanced, regular +100 videos, advanced + 200 videos, Material with practice questions', 'COR26'),
    ('CAT26', 'Test Series', 'basic, enhanced', 'MOCK26');

-- Insert coursefee
INSERT INTO coursefee (city, course, subcourse, variant, actual_lumpsum, actual_instalments, discount, lumpsum, instalments, first_instalment, second_instalment, third_instalment, status, mode) VALUES
    ('Hyderabad', 'CAT', 'CAT25', 'Online Live Course', 82000, 85000, 0, 76000, 80000, 40000, 40000, 0, 'active', 'offline'),
    ('Hyderabad', 'CAT', 'CAT26', 'Classroom Course', 74900, 77900, 0, 64900, 67900, 30000, 20000, 17900, 'active', 'online'),
    ('Hyderabad', 'CAT', 'CAT27', 'Online Live Course', 43950, 46950, 0, 43950, 46950, 19950, 16000, 11000, 'active', 'online');

-- Insert discounts
INSERT INTO discounts (course, subcourse, variant, discounttype, discount_range, city, discount_amount, test_name, discount_reason, discount_start_date, discount_end_date) VALUES
    ('CAT', 'CAT26', 'Online Live Course', 'scholarship test', '0-20%', 'Hyderabad', NULL, 'test1', NULL, '2025-05-10', '2025-05-20'),
    ('CAT', 'CAT26', 'Online Live Course', 'group discount', '0-40%', 'Hyderabad', NULL, NULL, NULL, '2025-05-10', '2025-05-20'),
    ('CAT', 'CAT26', 'Online Live Course', 'siblings discount', '0-30%', 'Hyderabad', NULL, NULL, NULL, '2025-05-10', '2025-05-20'),
    ('CAT', 'CAT26', 'Online Live Course', 'scholarship test', '0-20%', 'Hyderabad', NULL, 'test2', NULL, '2025-05-10', '2025-05-20'),
    ('CAT', 'CAT26', 'Online Live Course', 'special discount', NULL, 'Hyderabad', 2000, NULL, 'month end', '2025-05-10', '2025-05-20');

-- Insert exam_info
INSERT INTO exam_info (course, eligibility_criteria, exam_dates, registration_process, score_validity, top_b_schools, mba_advantages, selection_process, attempts_allowed) VALUES
    ('CAT', 'For CAT as per the notification any Graduate with 50% marks or SC/ST with 45% marks are eligible',
            'CAT exam will be held on last Sunday of November every year',
            'You can register for the CAT exam by visiting their official website',
            'Validity of CAT score is 1 year',
            'To be provided',
            'To be provided',
            'To be provided',
            'There is no Age / Attempts limit for CAT Exam');

-- Insert batch sizes
INSERT INTO batch_sizes (city, course, subcourse, variant, batch_size) VALUES
('Hyderabad', 'CAT', 'CAT26', 'Online Live Course', 30),
('Hyderabad', 'CAT', 'CAT26', 'Classroom Course', 30);