import sqlite3
import datetime
import os
import sys

# Base paths
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "attendance.db")


def get_db_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Existing tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]

    if "students" not in tables:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grno INTEGER UNIQUE,
                rollno INTEGER,
                name TEXT NOT NULL,
                std INTEGER,
                section TEXT,
                gender TEXT,
                phoneno TEXT,
                photo_path TEXT,
                class_id INTEGER,
                created_at TEXT,
                FOREIGN KEY (class_id) REFERENCES classes(id)
            )
            """
        )

    if "classes" not in tables:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT
            )
            """
        )

    if "attendance" not in tables:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT,
                time TEXT,
                status TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
            """
        )
    else:
        cur.execute("PRAGMA table_info(attendance)")
        columns = [col[1] for col in cur.fetchall()]
        if "studentid" in columns and "student_id" not in columns:
            cur.execute(
                "ALTER TABLE attendance RENAME COLUMN studentid TO student_id"
            )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    # Default class
    cur.execute("SELECT COUNT(*) FROM classes")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO classes (name, description, created_at) VALUES (?, ?, ?)",
            ("Default Class", "Default class for students", str(datetime.datetime.now())),
        )

    conn.commit()
    conn.close()


def add_student(grno, rollno, name, std, section, gender, phoneno, class_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO students (grno, rollno, name, std, section, gender, phoneno, class_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (grno, rollno, name, std, section, gender, phoneno, class_id, str(datetime.datetime.now())),
    )
    conn.commit()
    student_id = cur.lastrowid
    conn.close()
    return student_id


def get_all_students(search_term=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if search_term:
        s = f"%{search_term}%" # Adding wildcards for partial matching
        cur.execute(
            """
            SELECT id, grno, rollno, name, std, section, gender, phoneno, photo_path
            FROM students
            WHERE LOWER(name) LIKE ? OR CAST(grno AS TEXT) LIKE ? OR CAST(rollno AS TEXT) LIKE ?
            ORDER BY name
            """,
            (s, s, s),
        )
    else:
        cur.execute(
            """
            SELECT id, grno, rollno, name, std, section, gender, phoneno, photo_path
            FROM students
            ORDER BY name
            """
        )
    students = cur.fetchall()
    conn.close()
    return students


def get_student_by_id(student_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cur.fetchone()
    conn.close()
    return student

def get_student_by_name(name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE name LIKE ?", (f"%{name}%",)) # fuzzy search
    student = cur.fetchone()
    conn.close()
    return student

def update_student(student_id, grno, rollno, name, std, section, gender, phoneno):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE students
        SET grno = ?, rollno = ?, name = ?, std = ?, section = ?, gender = ?, phoneno = ?
        WHERE id = ?
        """,
        (grno, rollno, name, std, section, gender, phoneno, student_id),
    )
    conn.commit()
    conn.close()


def delete_student(student_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
    cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()


def get_student_count():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students")
    count = cur.fetchone()[0]
    conn.close()
    return count


def mark_attendance(student_id, date, time, status="P"):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO attendance (student_id, date, time, status)
        VALUES (?, ?, ?, ?)
        """,
        (student_id, date, time, status),
    )
    conn.commit()
    conn.close()


def check_attendance_exists(student_id, date):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM attendance WHERE student_id = ? AND date = ?",
        (student_id, date),
    )
    row = cur.fetchone()
    conn.close()
    return row is not None


def get_attendance_count_today():
    conn = get_db_connection()
    cur = conn.cursor()
    today = str(datetime.date.today())
    cur.execute(
        "SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date = ? AND status = 'P'",
        (today,),
    )
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_total_attendance_today():
    conn = get_db_connection()
    cur = conn.cursor()
    today = str(datetime.date.today())
    cur.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (today,))
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_attendance_last_n_days(ndays=7):
    conn = get_db_connection()
    cur = conn.cursor()
    dates = []
    counts = []
    for i in range(ndays):
        date = datetime.date.today() - datetime.timedelta(days=ndays - 1 - i)
        dates.append(date.strftime("%m/%d"))
        cur.execute(
            "SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date = ? AND status = 'P'",
            (str(date),),
        )
        counts.append(cur.fetchone()[0])
    conn.close()
    return dates, counts


def get_attendance_trend_by_name(name, ndays=7):
    conn = get_db_connection()
    cur = conn.cursor()

    # get student id
    cur.execute("SELECT id FROM students WHERE name LIKE ?", (f"%{name}%",))
    row = cur.fetchone()
    if not row:
        conn.close()
        return [], []
    student_id = row[0]

    dates = []
    counts = []
    for i in range(ndays):
        date = datetime.date.today() - datetime.timedelta(days=ndays - 1 - i)
        dates.append(date.strftime("%m/%d"))
        cur.execute(
            """
            SELECT COUNT(*)
            FROM attendance
            WHERE student_id = ? AND date = ? AND status = 'P'
            """,
            (student_id, str(date)),
        )
        counts.append(cur.fetchone()[0])
    conn.close()
    return dates, counts


def get_recent_attendance(limit=5):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.name, a.date, a.time, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC, a.time DESC
        LIMIT ?
        """,
        (limit,),
    )
    records = cur.fetchall()
    conn.close()
    return records


def get_attendance_reports(from_date, to_date, name_filter=None):
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
        SELECT
            s.name,
            s.grno,
            s.rollno,
            s.std || '-' || s.section,
            a.date,
            a.time,
            a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date BETWEEN ? AND ?
    """
    params = [from_date, to_date]
    if name_filter:
        query += " AND s.name LIKE ?"
        params.append(f"%{name_filter}%")
    query += " ORDER BY a.date DESC, a.time DESC"
    cur.execute(query, params)
    records = cur.fetchall()
    conn.close()
    return records


def get_all_classes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM classes")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_classes_detailed():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, description, created_at FROM classes ORDER BY name"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def add_class(name, description):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO classes (name, description, created_at) VALUES (?, ?, ?)",
        (name, description, str(datetime.datetime.now())),
    )
    conn.commit()
    conn.close()


def delete_class(class_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM classes WHERE id = ?", (class_id,))
    conn.commit()
    conn.close()


def get_class_student_count(class_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students WHERE class_id = ?", (class_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_class_id_by_name(class_name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM classes WHERE name = ?", (class_name,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def bulk_import_students(students_data):
    conn = get_db_connection()
    cur = conn.cursor()
    count = 0
    for row in students_data:
        try:
            cur.execute(
                """
                INSERT INTO students (
                    grno, rollno, name, std, section, gender, phoneno,
                    class_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    int(row["grno"]),
                    int(row["rollno"]),
                    row["name"],
                    int(row["std"]),
                    row["section"],
                    row["gender"],
                    row["phoneno"],
                    str(datetime.datetime.now()),
                ),
            )
            count += 1
        except Exception:
            continue
    conn.commit()
    conn.close()
    return count