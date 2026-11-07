# Student Management System

A full-stack Python project for managing student records and analysing academic performance.
It started as a menu-driven console app; this version adds a **Flask REST API**, a **SQLite**
database and a responsive **dark web dashboard**. The original console menu is still included.

## Features

- Add, view, search, update and delete student records
- Automatic grades (A+ to F), percentage, pass/fail result and **class rank** (ties share a rank)
- Sort by rank, marks, name or roll number; filter by grade and result
- Highest, lowest and average scores, pass rate, top performers
- Grade distribution and subject-wise average charts
- Student detail view with per-subject marks
- Live grade preview while entering marks, with field-level validation messages
- CSV export and one-click sample data
- Works on phones, tablets and desktops
- Console version (`cli.py`) that shares the same logic and database

## Tech stack

| Layer     | Technology                                  |
|-----------|---------------------------------------------|
| Backend   | Python 3.9+, Flask                          |
| Database  | SQLite (Python `sqlite3`, no ORM needed)    |
| Frontend  | HTML, CSS, vanilla JavaScript (no build step) |
| Testing   | `unittest` with Flask's test client         |
| Concepts  | Functions, lists and dictionaries, REST, validation, Git/GitHub |

## Project structure

```
student-management-system/
├── app.py             # Flask app and REST API routes
├── services.py        # Validation, grading, ranking, stats, CSV (business logic)
├── database.py        # SQLite connection and schema
├── cli.py             # Menu-driven console version
├── requirements.txt
├── templates/
│   └── index.html     # Dashboard page
├── static/
│   ├── css/style.css  # Dark theme, responsive layout
│   └── js/app.js      # Frontend logic (fetch API, rendering, dialogs)
└── tests/
    └── test_api.py    # Automated API tests
```

## Getting started

```bash
# 1. (optional) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run the web app
python app.py
```

Open **http://127.0.0.1:5000**. The database file `students.db` is created automatically.
Click **Load sample data** on the empty screen to try it out.

Console version:

```bash
python cli.py
```

Run the tests:

```bash
python -m unittest discover -s tests -v
```

## Grading rules

| Average | Grade | | Average | Grade |
|---------|-------|-|---------|-------|
| 90+     | A+    | | 50 to 59 | C    |
| 80 to 89 | A    | | 40 to 49 | D    |
| 70 to 79 | B+   | | below 40 | F    |
| 60 to 69 | B    | |          |      |

Each student has five subjects (Python, DBMS, Mathematics, Web Tech, English), each out of 100.
A student **passes** when every subject is 40 or above. Change `PASS_MARK` and `grade_for()` in
`services.py` to match your own rules.

## REST API

| Method | Endpoint                 | Description                                            |
|--------|--------------------------|--------------------------------------------------------|
| GET    | `/api/students`          | List students. Query: `q`, `sort`, `order`, `grade`, `status` |
| POST   | `/api/students`          | Create a student                                       |
| GET    | `/api/students/<id>`     | Get one student                                        |
| PUT    | `/api/students/<id>`     | Update a student                                       |
| DELETE | `/api/students/<id>`     | Delete a student                                       |
| GET    | `/api/stats`             | Class statistics, toppers, distributions               |
| POST   | `/api/seed`              | Insert sample students                                 |
| GET    | `/api/export.csv`        | Download all records as CSV                            |

Example:

```bash
curl -X POST http://127.0.0.1:5000/api/students \
  -H "Content-Type: application/json" \
  -d '{"roll_no":"BCA101","name":"Riya Kumari","course":"BCA","semester":3,
       "python":92,"dbms":85,"maths":78,"web":88,"english":81}'
```

Validation errors return HTTP 422 with a `fields` object; unknown ids return 404.

## Ideas to extend it

- Login for teachers (Flask-Login) and a read-only student view
- Attendance tracking and semester-wise result history
- Charts with Chart.js and PDF report cards
- Move to PostgreSQL or MySQL with SQLAlchemy
- Deploy on Render, Railway or PythonAnywhere (use `gunicorn app:app`)

## Author

Built as a Python portfolio project. Add your name, GitHub and LinkedIn links here.

## License

MIT. Free to use for learning and portfolios.
