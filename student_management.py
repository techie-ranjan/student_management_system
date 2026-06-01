students = []


def add_student():
    student_id = input("Enter Student ID: ")
    name = input("Enter Name: ")
    age = input("Enter Age: ")
    course = input("Enter Course: ")
    marks = float(input("Enter Marks: "))

    if marks >= 90:
        grade = "A+"
    elif marks >= 80:
        grade = "A"
    elif marks >= 70:
        grade = "B"
    elif marks >= 60:
        grade = "C"
    elif marks >= 50:
        grade = "D"
    else:
        grade = "F"

    student = {
        "id": student_id,
        "name": name,
        "age": age,
        "course": course,
        "marks": marks,
        "grade": grade
    }

    students.append(student)
    print("Student Added Successfully!")


def view_students():
    if len(students) == 0:
        print("No Student Records Found")
        return

    print("\n----- STUDENT RECORDS -----")
    for student in students:
        print("ID :", student["id"])
        print("Name :", student["name"])
        print("Age :", student["age"])
        print("Course :", student["course"])
        print("Marks :", student["marks"])
        print("Grade :", student["grade"])
        print("-------------------------")


def search_student():
    student_id = input("Enter Student ID to Search: ")

    for student in students:
        if student["id"] == student_id:
            print("\nStudent Found")
            print(student)
            return

    print("Student Not Found")


def update_student():
    student_id = input("Enter Student ID to Update: ")

    for student in students:
        if student["id"] == student_id:
            student["name"] = input("Enter New Name: ")
            student["course"] = input("Enter New Course: ")

            print("Student Updated Successfully")
            return

    print("Student Not Found")


def delete_student():
    student_id = input("Enter Student ID to Delete: ")

    for student in students:
        if student["id"] == student_id:
            students.remove(student)
            print("Student Deleted Successfully")
            return

    print("Student Not Found")


def sort_students():
    sorted_students = sorted(
        students,
        key=lambda x: x["marks"],
        reverse=True
    )

    print("\n----- RANK LIST -----")
    rank = 1

    for student in sorted_students:
        print(rank, student["name"], "-", student["marks"])
        rank += 1


def statistics():
    if len(students) == 0:
        print("No Records Available")
        return

    total = 0

    for student in students:
        total += student["marks"]

    average = total / len(students)

    highest = max(student["marks"] for student in students)
    lowest = min(student["marks"] for student in students)

    print("\n----- STATISTICS -----")
    print("Total Students :", len(students))
    print("Highest Marks :", highest)
    print("Lowest Marks :", lowest)
    print("Average Marks :", round(average, 2))


while True:
    print("\n===== STUDENT MANAGEMENT SYSTEM =====")
    print("1. Add Student")
    print("2. View Students")
    print("3. Search Student")
    print("4. Update Student")
    print("5. Delete Student")
    print("6. Sort Students")
    print("7. Statistics")
    print("8. Exit")

    choice = input("Enter Your Choice: ")

    if choice == "1":
        add_student()

    elif choice == "2":
        view_students()

    elif choice == "3":
        search_student()

    elif choice == "4":
        update_student()

    elif choice == "5":
        delete_student()

    elif choice == "6":
        sort_students()

    elif choice == "7":
        statistics()

    elif choice == "8":
        print("Thank You")
        break

    else:
        print("Invalid Choice")