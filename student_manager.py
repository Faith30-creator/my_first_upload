import json

FILE_NAME = "students.json"


def load_students():
    try:
        with open(FILE_NAME, "r") as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
            return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_students(students):
    with open(FILE_NAME, "w") as file:
        json.dump(students, file, indent=4)


def choose_name(name, existing_names):
    if name in existing_names:
        print(f"'{name}' is already being used.")
        suggestion = name + "1"
        print(f"Suggested name: {suggestion}")

        new_name = input("Enter a new name (or press Enter to use suggestion): ").strip()
        if not new_name:
            new_name = suggestion

        if new_name in existing_names:
            print(f"'{new_name}' is also already being used.")
            return None

        return new_name

    return name


def add_student():
    students = load_students()
    existing_names = [s["Name"].lower() for s in students if "Name" in s]

    # Name validation
    while True:
        name = input("Enter name: ").strip()

        if not name:
            print("Name cannot be empty.")
            continue

        if name.lower() in existing_names:
            resolved_name = choose_name(name, existing_names)
            if resolved_name is None:
                continue
            name = resolved_name

        break

    # Age validation
    while True:
        try:
            age = int(input("Enter age: "))
            if 1 <= age <= 100:
                break
            print("Enter an age between 1 and 100.")
        except ValueError:
            print("Please enter a valid number.")

    # School validation
    while True:
        school = input("Enter school: ").strip()
        if school:
            break
        print("School cannot be empty.")

    # Find highest ID
    highest_id = 0
    for student in students:
        if student.get("id", 0) > highest_id:
            highest_id = student["id"]

    new_id = highest_id + 1

    new_student = {
        "id": new_id,
        "Name": name,
        "age": age,
        "school": school,
    }

    students.append(new_student)
    save_students(students)

    print(f"Student '{name}' added successfully with ID {new_id}!")


def view_students():
    students = load_students()

    if not students:
        print("\nNo students found.")
        return

    print("\n===== STUDENT LIST =====")
    for student in students:
        print("ID:", student.get("id"))
        print("Name:", student.get("Name"))
        print("Age:", student.get("age"))
        print("School:", student.get("school"))
        print("----------------")


def update_student():
    students = load_students()

    try:
        student_id = int(input("Enter student ID to update: "))
    except ValueError:
        print("Invalid ID format!")
        return

    for student in students:
        if student["id"] == student_id:
            print(f"Updating records for student: {student['Name']} (ID: {student_id})")

            # Get names of ALL OTHER students to prevent duplicate names on update
            other_names = [
                s["Name"].lower()
                for s in students
                if s["id"] != student_id and "Name" in s
            ]

            # Name update with existing name pre-filled / default
            while True:
                new_name = input(
                    f"Enter new name (current: '{student['Name']}', press Enter to keep current): "
                ).strip()

                if not new_name:
                    new_name = student["Name"]
                    break

                if new_name.lower() in other_names:
                    resolved_name = choose_name(new_name, other_names)
                    if resolved_name is None:
                        continue
                    new_name = resolved_name

                break

            # Age update
            while True:
                age_input = input(
                    f"Enter new age (current: {student['age']}, press Enter to keep current): "
                ).strip()

                if not age_input:
                    new_age = student["age"]
                    break

                try:
                    new_age = int(age_input)
                    if 1 <= new_age <= 100:
                        break
                    print("Enter an age between 1 and 100.")
                except ValueError:
                    print("Please enter a valid number.")

            # School update
            school_input = input(
                f"Enter new school (current: '{student['school']}', press Enter to keep current): "
            ).strip()
            new_school = school_input if school_input else student["school"]

            # Save updated values
            student["Name"] = new_name
            student["age"] = new_age
            student["school"] = new_school

            save_students(students)
            print("Student updated successfully!")
            return

    print("Student not found!")


def delete_student():
    students = load_students()

    try:
        student_id = int(input("Enter student ID to delete: "))
    except ValueError:
        print("Invalid ID format!")
        return

    for student in students:
        if student["id"] == student_id:
            students.remove(student)
            save_students(students)
            print("Student deleted successfully!")
            return

    print("Student not found!")


def search_student():
    students = load_students()

    print("\n===== SEARCH STUDENT =====")
    print("1. Search by ID")
    print("2. Search by Name")
    print("3. Search by School")

    choice = input("Choose search option: ").strip()

    if choice == "1":
        try:
            student_id = int(input("Enter student ID: "))
        except ValueError:
            print("Invalid ID format!")
            return

        for student in students:
            if student["id"] == student_id:
                print("\nID:", student["id"])
                print("Name:", student["Name"])
                print("Age:", student["age"])
                print("School:", student["school"])
                return

        print("Student not found!")

    elif choice == "2":
        name = input("Enter student name: ").strip()

        for student in students:
            if student["Name"].lower() == name.lower():
                print("\nID:", student["id"])
                print("Name:", student["Name"])
                print("Age:", student["age"])
                print("School:", student["school"])
                return

        print("Student not found!")

    elif choice == "3":
        school = input("Enter school: ").strip()
        found = False

        for student in students:
            if student["school"].lower() == school.lower():
                print("\nID:", student["id"])
                print("Name:", student["Name"])
                print("Age:", student["age"])
                print("School:", student["school"])
                print("----------------")
                found = True

        if not found:
            print("No students found!")


while True:
    print("\n===== STUDENT MANAGER =====")
    print("1. Add Student")
    print("2. View Students")
    print("3. Update Student")
    print("4. Delete Student")
    print("5. Search Student")
    print("6. Exit")

    choice = input("Choose an option: ").strip()

    if choice == "1":
        add_student()
    elif choice == "2":
        view_students()
    elif choice == "3":
        update_student()
    elif choice == "4":
        delete_student()
    elif choice == "5":
        search_student()
    elif choice == "6":
        print("Goodbye!")
        break
    else:
        print("Invalid choice!")
