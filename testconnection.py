# Test DB1 (MySQL)
import pymysql
conn = pymysql.connect(
    host='36.50.3.169',
    user='dbuser',
    password="5v)P11,D",
    database='timeonli_sample'
)
conn.close()
print("DB1 connected")

# Test DB3 (Local MySQL)
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='Rudra@1879',
    database='time_db3'
)
conn.close()
print("DB3 connected")

# Test DB2 (MSSQL)
import pyodbc
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=36.50.3.169;'
    'DATABASE=VendorDB;'
    'UID=vendorlogin;'
    'PWD=Vendor@123'
)
conn.close()
print("DB2 connected")