"""Business logic: validation, grading, ranking, statistics, CSV export."""
import csv
import io
import re
import sqlite3

from database import SUBJECTS, get_conn

SUBJECT_LABELS = {
    "python": "Python",
    "dbms": "DBMS",
    "maths": "Mathematics",
    "web": "Web Tech",
    "english": "English",
}
COURSES = ["BCA", "BBA", "B.Sc CS", "B.Tech", "MCA"]
GRADES = ["A+", "A", "B+", "B", "C", "D", "F"]
PASS_MARK = 40
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    def __init__(self, errors):
        super().__init__("Validation failed")
        self.errors = errors


class NotFound(Exception):
    pass


# ---------------------------------------------------------------- grading
def grade_for(pct):
    for limit, grade in ((90, "A+"), (80, "A"), (70, "B+"), (60, "B"), (50, "C"), (40, "D")):
        if pct >= limit:
            return grade
    return "F"


def _decorate(row):
    d = dict(row)
    total = sum(d[s] for s in SUBJECTS)
    pct = round(total / len(SUBJECTS), 2)
    d["total"] = round(total, 2)
    d["percentage"] = pct
    d["grade"] = grade_for(pct)
    d["passed"] = all(d[s] >= PASS_MARK for s in SUBJECTS)
    return d


def _all_ranked():
    """All students with computed fields and a competition rank (ties share a rank)."""
    with get_conn() as conn:
        rows = [_decorate(r) for r in conn.execute("SELECT * FROM students")]
    for s in rows:
        s["rank"] = 1 + sum(1 for o in rows if o["percentage"] > s["percentage"])
    return rows


# ------------------------------------------------------------- validation
def validate(payload):
    errors, clean = {}, {}
    payload = payload or {}

    roll = str(payload.get("roll_no", "")).strip()
    if not roll:
        errors["roll_no"] = "Enter a roll number."
    elif len(roll) > 20:
        errors["roll_no"] = "Roll number can be at most 20 characters."
    clean["roll_no"] = roll

    name = " ".join(str(payload.get("name", "")).split())
    if len(name) < 2:
        errors["name"] = "Enter the student's full name."
    elif len(name) > 60:
        errors["name"] = "Name can be at most 60 characters."
    clean["name"] = name

    email = str(payload.get("email", "")).strip()
    if email and not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address, or leave it empty."
    clean["email"] = email

    course = str(payload.get("course", "BCA")).strip() or "BCA"
    if course not in COURSES:
        errors["course"] = "Choose one of: " + ", ".join(COURSES) + "."
    clean["course"] = course

    try:
        sem = int(payload.get("semester", 1))
        if not 1 <= sem <= 8:
            raise ValueError
        clean["semester"] = sem
    except (TypeError, ValueError):
        errors["semester"] = "Semester must be a number from 1 to 8."

    for s in SUBJECTS:
        try:
            raw = payload.get(s, 0)
            val = float(0 if raw in ("", None) else raw)
            if not 0 <= val <= 100:
                raise ValueError
            clean[s] = round(val, 2)
        except (TypeError, ValueError):
            errors[s] = f"{SUBJECT_LABELS[s]} marks must be between 0 and 100."

    if errors:
        raise ValidationError(errors)
    return clean


# -------------------------------------------------------------------- CRUD
def list_students(q="", sort="rank", order="asc", grade="", status=""):
    students = _all_ranked()
    q = (q or "").strip().lower()
    if q:
        students = [
            s for s in students
            if q in s["name"].lower() or q in s["roll_no"].lower()
            or q in s["course"].lower() or q in s["email"].lower()
        ]
    if grade:
        students = [s for s in students if s["grade"] == grade]
    if status == "pass":
        students = [s for s in students if s["passed"]]
    elif status == "fail":
        students = [s for s in students if not s["passed"]]

    allowed = {"rank", "name", "roll_no", "percentage", "total", "semester", "course"} | set(SUBJECTS)
    if sort not in allowed:
        sort = "rank"
    key = (lambda s: (s["rank"], s["name"].lower())) if sort == "rank" else (
        lambda s: s[sort].lower() if isinstance(s[sort], str) else s[sort]
    )
    students.sort(key=key, reverse=(order == "desc"))
    return students


def get_student(student_id):
    for s in _all_ranked():
        if s["id"] == student_id:
            return s
    raise NotFound(f"Student {student_id} not found.")


def create_student(payload):
    data = validate(payload)
    cols = ", ".join(data)
    marks = ", ".join("?" for _ in data)
    try:
        with get_conn() as conn:
            cur = conn.execute(f"INSERT INTO students ({cols}) VALUES ({marks})", list(data.values()))
            new_id = cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValidationError({"roll_no": "This roll number already exists."})
    return get_student(new_id)


def update_student(student_id, payload):
    get_student(student_id)
    data = validate(payload)
    sets = ", ".join(f"{k} = ?" for k in data)
    try:
        with get_conn() as conn:
            conn.execute(f"UPDATE students SET {sets} WHERE id = ?", [*data.values(), student_id])
    except sqlite3.IntegrityError:
        raise ValidationError({"roll_no": "This roll number already exists."})
    return get_student(student_id)


def delete_student(student_id):
    get_student(student_id)
    with get_conn() as conn:
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))


# ------------------------------------------------------------------- stats
def stats():
    students = _all_ranked()
    n = len(students)
    dist = {g: 0 for g in GRADES}
    for s in students:
        dist[s["grade"]] += 1
    out = {
        "count": n,
        "average": 0,
        "highest": None,
        "lowest": None,
        "pass_rate": 0,
        "grade_distribution": dist,
        "subject_averages": {s: 0 for s in SUBJECTS},
        "toppers": [],
    }
    if not n:
        return out
    ordered = sorted(students, key=lambda s: (s["rank"], s["name"].lower()))
    brief = lambda s: {"id": s["id"], "name": s["name"], "roll_no": s["roll_no"],
                       "percentage": s["percentage"], "grade": s["grade"], "rank": s["rank"]}
    out["average"] = round(sum(s["percentage"] for s in students) / n, 2)
    out["highest"] = brief(ordered[0])
    out["lowest"] = brief(ordered[-1])
    out["pass_rate"] = round(100 * sum(1 for s in students if s["passed"]) / n, 1)
    out["subject_averages"] = {
        s: round(sum(st[s] for st in students) / n, 2) for s in SUBJECTS
    }
    out["toppers"] = [brief(s) for s in ordered[:5]]
    return out


# ------------------------------------------------------------- CSV / seed
def export_csv():
    students = list_students()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Rank", "Roll No", "Name", "Email", "Course", "Semester",
                *[SUBJECT_LABELS[s] for s in SUBJECTS], "Total", "Percentage", "Grade", "Result"])
    for s in students:
        w.writerow([s["rank"], s["roll_no"], s["name"], s["email"], s["course"], s["semester"],
                    *[s[x] for x in SUBJECTS], s["total"], s["percentage"], s["grade"],
                    "Pass" if s["passed"] else "Fail"])
    return buf.getvalue()


DEMO = [
    ("BCA001", "Ananya Sharma", "ananya@example.com", "BCA", 3, 94, 91, 88, 96, 90),
    ("BCA002", "Rohan Verma", "rohan@example.com", "BCA", 3, 82, 78, 74, 85, 80),
    ("BCA003", "Priya Singh", "priya@example.com", "BCA", 3, 71, 69, 65, 77, 73),
    ("BCA004", "Aman Gupta", "aman@example.com", "BCA", 3, 58, 62, 49, 66, 60),
    ("BCA005", "Sneha Kumari", "sneha@example.com", "BCA", 3, 88, 84, 79, 90, 86),
    ("BCA006", "Vikram Yadav", "vikram@example.com", "BCA", 3, 45, 38, 41, 52, 48),
    ("BCA007", "Kavya Mishra", "kavya@example.com", "BCA", 3, 67, 72, 58, 70, 75),
    ("BCA008", "Arjun Das", "arjun@example.com", "BCA", 3, 35, 42, 30, 44, 50),
]


def seed_demo():
    added = 0
    keys = ["roll_no", "name", "email", "course", "semester", *SUBJECTS]
    for row in DEMO:
        try:
            create_student(dict(zip(keys, row)))
            added += 1
        except ValidationError:
            pass  # roll number already present
    return added
