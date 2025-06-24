use timeonli_sample;
CREATE TABLE ttse_creation (
    sno INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    course VARCHAR(50) NOT NULL,
    ttse_date DATE NULL,
    description VARCHAR(500) NOT NULL,
    create_date DATETIME NULL,
    created_by VARCHAR(100) NULL,
    usertype VARCHAR(50) NULL,
    url_name VARCHAR(500) NULL,
    ttse_codes VARCHAR(200) NULL,
    cat_chni_fb VARCHAR(1000) NULL,
    cat_chni_wp VARCHAR(1000) NULL,
    cat_kol_fb VARCHAR(1000) NULL,
    cat_othr_fb VARCHAR(1000) NULL,
    ttse_rstdate DATE NULL,
    ttse_rendate DATE NULL,
    status VARCHAR(10) NULL,
    ttse_type VARCHAR(50) NULL,
    city VARCHAR(100) NULL,
    college_name VARCHAR(500) NULL,
    slot1 VARCHAR(50) NULL,
    slot2 VARCHAR(50) NULL,
    discount VARCHAR(500) NULL,
    slot3 VARCHAR(50) NULL,
    coll_url VARCHAR(500) NULL,
    eventurl VARCHAR(500) NULL
);

INSERT INTO ttse_creation (course, ttse_date, description, create_date, created_by, usertype, url_name, ttse_codes, cat_chni_fb, cat_chni_wp, cat_kol_fb, cat_othr_fb, ttse_rstdate, ttse_rendate, status, ttse_type, city, college_name, slot1, slot2, discount, slot3, coll_url, eventurl) VALUES
    ('CAT', '2025-10-05', 'All India CAT TTSE', '2025-05-04 07:39:02', 'cc001', 'CAT_05102025_954', 'https://www.time4education.com/moodle/registrations/ttse_registration.asp?utype=CAT_05102025_954&crs=CAT', NULL, 'https://www.time4education.com/allindia-online-catttse/chennai-fb_ttse.asp?utype=CAT_05102025_954&crs=CAT', 'https://www.time4education.com/allindia-online-catttse/chennai-whatsapp_ttse.asp?utype=CAT_05102025_954&crs=CAT', 'https://www.time4education.com/allindia-online-catttse/kolkata_fb_ttse.asp?utype=CAT_05102025_954&crs=CAT', 'https://www.time4education.com/allindia-online-catttse/othercity-fb-ttse.asp?utype=CAT_05102025_954&crs=CAT&cid=', '2025-04-05', '2025-10-05', NULL, 'allindia', 'All', ',,,,,,', '10:00:00', '18:00:00', 'Gets a Flat Rs. 5000/- Discount on CAT 2025/26 Course fee', NULL, 'https://www.time4education.com/moodle/registrations/ttse_registration_coll.asp?utype=CAT_05102025_954&crs=CAT', 'https://www.time4education.com/local/articlecms/page.php?id=4430'),
    ('CAT', '2025-04-05', 'CAT TTSE Cochin Local', '2025-05-03 12:55:41', 'cc001', 'CAT_05042025_953', 'https://www.time4education.com/moodle/registrations/ttse_registration.asp?utype=CAT_05042025_953&crs=CAT', NULL, 'https://www.time4education.com/allindia-online-catttse/chennai-fb_ttse.asp?utype=CAT_05042025_953&crs=CAT', 'https://www.time4education.com/allindia-online-catttse/chennai-whatsapp_ttse.asp?utype=CAT_05042025_953&crs=CAT', 'https://www.time4education.com/allindia-online-catttse/kolkata_fb_ttse.asp?utype=CAT_05042025_953&crs=CAT', 'https://www.time4education.com/allindia-online-catttse/othercity-fb-ttse.asp?utype=CAT_05042025_953&crs=CAT&cid=', '2025-03-05', '2025-04-05', NULL, NULL, 'Cochin', ',,,,,,', '10:00:00', '18:00:00', NULL, NULL, 'https://www.time4education.com/moodle/registrations/ttse_registration_coll.asp?utype=CAT_05042025_953&crs=CAT', 'https://www.time4education.com/local/articlecms/page.php?id=8537'),
    ('BANK', '2025-03-05', 'Aptitude test by T.I.M.E,shillong,local', '2025-05-01 15:47:07', 'cc001', 'BANK_05032025_952', 'https://www.time4education.com/moodle/registrations/ttse_registration.asp?utype=BANK_05032025_952&crs=BANK', NULL, NULL, NULL, NULL, 'https://www.time4education.com/allindia-online-bankttse/othercity-fb-ttse.asp?utype=BANK_05032025_952&crs=BANK&cid=', '2025-01-05', '2025-03-05', NULL, NULL, 'Shillong', ',,,,,,', '16:00:00', '18:00:00', NULL, NULL, 'https://www.time4education.com/moodle/registrations/ttse_registration_coll.asp?utype=BANK_05032025_952&crs=BANK', 'https://www.time4education.com/local/articlecms/page.php?id=8533');