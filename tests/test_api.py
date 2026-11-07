import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database  # noqa: E402

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
database.DB_PATH = _tmp.name

import app as app_module  # noqa: E402
import services  # noqa: E402


def payload(**over):
    data = {"roll_no": "T1", "name": "Test Student", "email": "t@example.com", "course": "BCA",
            "semester": 2, "python": 80, "dbms": 70, "maths": 60, "web": 90, "english": 50}
    data.update(over)
    return data


class StudentAPITests(unittest.TestCase):
    def setUp(self):
        with database.get_conn() as c:
            c.execute("DELETE FROM students")
        self.client = app_module.app.test_client()

    def test_create_and_grade(self):
        r = self.client.post("/api/students", json=payload())
        self.assertEqual(r.status_code, 201)
        s = r.get_json()
        self.assertEqual(s["percentage"], 70.0)
        self.assertEqual(s["grade"], "B+")
        self.assertTrue(s["passed"])
        self.assertEqual(s["rank"], 1)

    def test_validation_errors(self):
        r = self.client.post("/api/students", json=payload(name="", python=150, email="bad"))
        self.assertEqual(r.status_code, 422)
        fields = r.get_json()["fields"]
        self.assertIn("name", fields)
        self.assertIn("python", fields)
        self.assertIn("email", fields)

    def test_duplicate_roll_number(self):
        self.client.post("/api/students", json=payload())
        r = self.client.post("/api/students", json=payload(name="Someone Else"))
        self.assertEqual(r.status_code, 422)
        self.assertIn("roll_no", r.get_json()["fields"])

    def test_update_delete_and_404(self):
        sid = self.client.post("/api/students", json=payload()).get_json()["id"]
        r = self.client.put(f"/api/students/{sid}", json=payload(name="Renamed", python=100))
        self.assertEqual(r.get_json()["name"], "Renamed")
        self.assertEqual(self.client.delete(f"/api/students/{sid}").status_code, 200)
        self.assertEqual(self.client.get(f"/api/students/{sid}").status_code, 404)

    def test_ranking_ties_search_sort(self):
        self.client.post("/api/students", json=payload(roll_no="A", name="Alpha", python=100))
        self.client.post("/api/students", json=payload(roll_no="B", name="Bravo", python=100))
        self.client.post("/api/students", json=payload(roll_no="C", name="Charlie", python=10))
        ranks = {s["name"]: s["rank"] for s in self.client.get("/api/students").get_json()}
        self.assertEqual(ranks, {"Alpha": 1, "Bravo": 1, "Charlie": 3})
        found = self.client.get("/api/students?q=char").get_json()
        self.assertEqual([s["name"] for s in found], ["Charlie"])
        low = self.client.get("/api/students?sort=percentage&order=asc").get_json()
        self.assertEqual(low[0]["name"], "Charlie")

    def test_stats_and_export(self):
        self.assertEqual(self.client.get("/api/stats").get_json()["count"], 0)
        self.client.post("/api/seed")
        st = self.client.get("/api/stats").get_json()
        self.assertEqual(st["count"], len(services.DEMO))
        self.assertGreater(st["highest"]["percentage"], st["lowest"]["percentage"])
        csv_text = self.client.get("/api/export.csv").get_data(as_text=True)
        self.assertTrue(csv_text.startswith("Rank,Roll No,Name"))

    def test_home_page(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Student Management System", r.data)


if __name__ == "__main__":
    unittest.main()
