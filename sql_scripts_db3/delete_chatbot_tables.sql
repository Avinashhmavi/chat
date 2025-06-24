-- Drop tables that were originally in db3 from the remote MySQL database (db1)
use timeonli_sample;
DROP TABLE IF EXISTS query_history;
DROP TABLE IF EXISTS exam_info;
DROP TABLE IF EXISTS static_answers;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS user_details;
DROP TABLE IF EXISTS subcourses;