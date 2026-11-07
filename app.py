"""Student Management System — Flask backend.

Run:  python app.py        then open http://127.0.0.1:5000
"""
from flask import Flask, Response, jsonify, render_template, request

import services
from database import SUBJECTS, init_db

app = Flask(__name__)
app.json.sort_keys = False


@app.get("/")
def index():
    return render_template("index.html", subjects=SUBJECTS, labels=services.SUBJECT_LABELS,
                           courses=services.COURSES, grades=services.GRADES)


# ------------------------------------------------------------------ REST API
@app.get("/api/students")
def api_list():
    a = request.args
    return jsonify(services.list_students(
        q=a.get("q", ""), sort=a.get("sort", "rank"), order=a.get("order", "asc"),
        grade=a.get("grade", ""), status=a.get("status", "")))


@app.post("/api/students")
def api_create():
    return jsonify(services.create_student(request.get_json(silent=True))), 201


@app.get("/api/students/<int:student_id>")
def api_get(student_id):
    return jsonify(services.get_student(student_id))


@app.put("/api/students/<int:student_id>")
def api_update(student_id):
    return jsonify(services.update_student(student_id, request.get_json(silent=True)))


@app.delete("/api/students/<int:student_id>")
def api_delete(student_id):
    services.delete_student(student_id)
    return jsonify({"deleted": student_id})


@app.get("/api/stats")
def api_stats():
    return jsonify(services.stats())


@app.post("/api/seed")
def api_seed():
    return jsonify({"added": services.seed_demo()})


@app.get("/api/export.csv")
def api_export():
    return Response(
        services.export_csv(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=students.csv"})


# ------------------------------------------------------------ error handlers
@app.errorhandler(services.ValidationError)
def on_validation(err):
    return jsonify({"error": "Please fix the highlighted fields.", "fields": err.errors}), 422


@app.errorhandler(services.NotFound)
def on_not_found(err):
    return jsonify({"error": str(err)}), 404


init_db()

if __name__ == "__main__":
    app.run(debug=True)
