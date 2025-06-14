-- Insert data into the existing remote MySQL database (db1)
use timeonli_sample;
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

-- Insert questions (excluding "What is the batch size?")
INSERT INTO questions (category_id, question_text, display_order, source_type, source_detail) VALUES
    -- Fees, Discounts & Scholarships
    (1, 'What is the course fee?', 1, 'DB', 'coursedetails'),
    (1, 'Is there an installment option?', 2, 'STATIC', NULL),
    (1, 'Are there any discounts?', 3, 'STATIC', NULL),
    (1, 'Is there a scholarship test?', 4, 'DB', 'ttse_creation'),
    (1, 'Referral discounts available?', 5, 'STATIC', NULL),
    -- Courses & Batches
    (2, 'What are the batch timings?', 1, 'STATIC', NULL),
    (2, 'What is the duration of the course and Validity?', 2, 'STATIC', NULL),
    (2, 'When is the next batch starting?', 3, 'STATIC', NULL),
    (2, 'Is it a weekday / weekend - How many days a week?', 4, 'STATIC', NULL),
    (2, 'Are demo classes available?', 5, 'STATIC', NULL),
    -- Study Material & Mock Tests
    (3, 'What material is provided?', 1, 'STATIC', NULL),
    (3, 'Number of mock tests?', 2, 'STATIC', NULL),
    (3, 'Are mocks aligned with the actual exam?', 3, 'STATIC', NULL),
    (3, 'Access to online tests?', 4, 'STATIC', NULL),
    (3, 'Mock analysis and solutions?', 5, 'STATIC', NULL),
    (3, 'Number of books provided?', 6, 'STATIC', NULL),
    (3, 'Are Mocks all India based?', 7, 'STATIC', NULL),
    (3, 'How many mocks are Self administered?', 8, 'STATIC', NULL),
    (3, 'Do you train for other management entrance exams?', 9, 'STATIC', NULL),
    (3, 'Do you have video sessions?', 10, 'STATIC', NULL),
    -- Results & Support
    (4, 'Previous results / student performance?', 1, 'STATIC', NULL),
    (4, 'Testimonials or success stories?', 2, 'DB', 'testimonials'),
    (4, 'Doubt Clarifications?', 3, 'STATIC', NULL),
    (4, 'Mentoring Session on B-school selection?', 4, 'STATIC', NULL),
    (4, 'Application assistance for B-schools/universities?', 5, 'STATIC', NULL),
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
    (7, 'What are its features?', 2, 'STATIC', NULL),
    (7, 'Access to live & recorded sessions?', 3, 'STATIC', NULL),
    -- Exam & Other Info
    (8, 'What are the eligibility criteria?', 1, 'DB', 'exam_info'),
    (8, 'When are the exam dates?', 2, 'DB', 'exam_info'),
    (8, 'How to register for the exam?', 3, 'DB', 'exam_info'),
    (8, 'What is the score validity?', 4, 'DB', 'exam_info'),
    (8, 'List of Top B-schools?', 5, 'DB', 'exam_info'),
    (8, 'Advantages of MBA?', 6, 'DB', 'exam_info'),
    (8, 'B-school selection process?', 7, 'DB', 'exam_info'),
    (8, 'How many attempts are allowed?', 8, 'DB', 'exam_info');

-- Insert static answers
INSERT INTO static_answers (question_id, answer_text) VALUES
    (2, 'Yes, available, Please contact the {city} center for further details.'),
    (3, 'Yes, available, Please contact the {city} center for further details.'),
    (5, 'Please reach us further details at 040 - 40088300/401'),
    (10, 'Yes'),
    (23, 'Doubt Clarification through email/chat/telegram groups'),
    (24, 'Yes mentoring sessions will be conducted for B-school selection'),
    (26, 'Yes will be provided as part of the GWPI module'),
    (27, 'You can take back-up class when conducted for other batch'),
    (28, 'Special workshops will be conducted on different topics'),
    (29, 'We provide mentorship as per the requirement'),
    (31, 'We have library facility available. Lab facility available to take invigilated Mock Tests'),
    (33, 'No, we dont have hostel facility or we have tie-up with Hostels'),
    (34, 'Wi-Fi or internet facility is not available'),
    (35, 'Yes we have telegram channel support: TIME4CAT\nTIME4CAT is our app and www.time4education.com is our website'),
    (37, 'Yes'),
    (36, "• Login Activity Insights: Tracks last login, alerts students on pending tests/videos, helps mentors identify inactive learners.
• Smart Resume: Resumes videos/tests from last activity across devices.
• Photo-Based Identity Verification: Captures student photo at first login; supports exam proctoring.
• Intelligent Attendance Monitoring: Geofenced & event-based attendance tracking (live, recorded, classroom).
• Mentorship Engine: Auto-reminders for missed classes, personalized content suggestions.
• Performance Analytics: Sub-topic level analysis, intelligent recommendations, leaderboard rankings.
• Smart Action Plans: Auto-generated revision plans based on weak areas.
• Bookmarking & Quick Contact: Tag PDFs/videos, add comments, raise doubts via chatbot or faculty.
• Free SHP Access: Limited dashboard access with targeted upgrade prompts.
• Secure Payments: In-app payment gateway (UPI, cards, wallets).
• Referral Program: Discounts for both referrers and new users.
• AI Learning Tools: Video summarization, transcript-based tests, daily vocab tests.
• Unified Platform: Single app for all courses (Android/iOS); no-code admin panel for content & ops.");

-- Insert subcourses
INSERT INTO subcourses (course, subcourse) VALUES
    ('CAT', 'CAT 2025'),
    ('CAT', 'CAT 2026'),
    ('CAT', 'CAT 2027');

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