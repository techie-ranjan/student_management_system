"""Menu-driven console version, sharing the same logic and database as the web app.

Run:  python cli.py
"""
import services
from database import SUBJECTS, init_db


def ask(prompt, default=""):
    v = input(f"{prompt}{f' [{default}]' if default != '' else ''}: ").strip()
    return v if v else default


def show(students):
    if not students:
        print("\n  No records found.\n")
        return
    print(f"\n{'Rank':<5}{'Roll':<10}{'Name':<24}{'Total':>7}{'%':>8}  Grade  Result")
    print("-" * 66)
    for s in students:
        print(f"{s['rank']:<5}{s['roll_no']:<10}{s['name'][:22]:<24}{s['total']:>7}"
              f"{s['percentage']:>8}  {s['grade']:<6} {'Pass' if s['passed'] else 'Fail'}")
    print()


def form(existing=None):
    e = existing or {}
    data = {
        "roll_no": ask("Roll no", e.get("roll_no", "")),
        "name": ask("Name", e.get("name", "")),
        "email": ask("Email (optional)", e.get("email", "")),
        "course": ask("Course", e.get("course", "BCA")),
        "semester": ask("Semester (1-8)", e.get("semester", 1)),
    }
    for s in SUBJECTS:
        data[s] = ask(f"{services.SUBJECT_LABELS[s]} marks (0-100)", e.get(s, 0))
    return data


def pick():
    roll = ask("Roll no of the student")
    for s in services.list_students(q=roll):
        if s["roll_no"].lower() == roll.lower():
            return s
    print("  No student with that roll number.")
    return None


def main():
    init_db()
    menu = """
=== Student Management System ===
 1. Add student        6. Sort by marks
 2. View all           7. Highest / lowest / average
 3. Search             8. Load demo data
 4. Update student     9. Exit
 5. Delete student
"""
    while True:
        print(menu)
        choice = ask("Choose")
        try:
            if choice == "1":
                s = services.create_student(form())
                print(f"  Added {s['name']} - grade {s['grade']}, rank {s['rank']}.")
            elif choice == "2":
                show(services.list_students())
            elif choice == "3":
                show(services.list_students(q=ask("Search by name, roll no or course")))
            elif choice == "4":
                s = pick()
                if s:
                    services.update_student(s["id"], form(s))
                    print("  Record updated.")
            elif choice == "5":
                s = pick()
                if s and ask(f"Delete {s['name']}? (y/n)", "n").lower() == "y":
                    services.delete_student(s["id"])
                    print("  Record deleted.")
            elif choice == "6":
                show(services.list_students(sort="percentage", order=ask("Order asc/desc", "desc")))
            elif choice == "7":
                st = services.stats()
                if not st["count"]:
                    print("  No data yet.")
                else:
                    print(f"\n  Students: {st['count']}   Class average: {st['average']}%")
                    print(f"  Highest: {st['highest']['name']} ({st['highest']['percentage']}%)")
                    print(f"  Lowest:  {st['lowest']['name']} ({st['lowest']['percentage']}%)")
                    print(f"  Pass rate: {st['pass_rate']}%")
            elif choice == "8":
                print(f"  Added {services.seed_demo()} demo students.")
            elif choice == "9":
                print("Goodbye!")
                break
            else:
                print("  Please choose a number from 1 to 9.")
        except services.ValidationError as err:
            for field, msg in err.errors.items():
                print(f"  {field}: {msg}")
        except services.NotFound as err:
            print(f"  {err}")


if __name__ == "__main__":
    main()
