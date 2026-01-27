'''
import sqlite3
import os
import sys

# Find your app's database path automatically
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "attendance.db")

print(f"------------Database location: {DB_PATH}--------------")
print(f"------------Database exists: {os.path.exists(DB_PATH)}------------")
print("\n" + "="*60)

try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Show all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print("--------Tables found:----------")
    for table in tables:
        print(f"  - {table[0]}")
    print()
    
    # Show students (master table)
    print("-----------STUDENTS (master table):-------------")
    cur.execute("SELECT * FROM master")
    students = cur.fetchall()
    if students:
        print(f"  Total: {len(students)} students")
        for i, student in enumerate(students[:5], 1):  # Show first 5
            print(f"  {i}. GR:{student[0]} Roll:{student[1]} Name:{student[2]} Std:{student[3]} Sec:{student[4]}")
        if len(students) > 5:
            print(f"  ... and {len(students)-5} more")
    else:
        print("  No students added yet")
    print()
    
    # Show attendance records
    print("------------ATTENDANCE (january table):---------------")
    cur.execute("SELECT * FROM january")
    attendance = cur.fetchall()
    if attendance:
        print(f"  Total: {len(attendance)} records")
        for i, record in enumerate(attendance[:5], 1):  # Show first 5
            print(f"  {i}. {record[2]} - {record[5]} - {record[6]}")
        if len(attendance) > 5:
            print(f"  ... and {len(attendance)-5} more")
    else:
        print("  No attendance records yet")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
'''
