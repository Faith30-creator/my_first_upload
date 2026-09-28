import json

FILE_NAME = "students.json"

def load_students():
    with open(FILE_NAME, "r") as file:
        try:
            data = json.load(file)
            if isinstance (data, list):
                return data
            return []
        except json.JSONDecodeError :
             return []
        return []


def save_students(students):
    with open(FILE_NAME, "w") as file:
        json.dump(students, file, indent=4)    
        
def add_student():
    students = load_students()

    # Name validation
    while True:
        name = input("Enter name: ").strip()

        if not name:
            print("Name cannot be empty.")
            continue

        name_exists = False

        for student in students:
            if student["Name"].lower() == name.lower():
                name_exists = True
                break

        if name_exists:
            print("Name is already in use. Please choose another name.")
        else:
            break        

    # Age validation
    while True:
        try:
            age = int(input("Enter age: "))

            if 1 <= age <= 100:
                break
            else:
                print("Enter an age between 1 and 100.")

        except ValueError:
            print("Please enter a valid number.")

    while True:
        school = input("Enter school: ").strip()

        if school:
            break

        print("School cannot be empty.")

    # Find highest ID
    highest_id = 0

    for student in students:
        if student["id"] > highest_id:
            highest_id = student["id"]

    new_id = highest_id + 1

    new_student = {
        "id": new_id,
        "Name": name,
        "age": age,
        "school": school
    }

    students.append(new_student)
    save_students(students)

    print("Student added successfully!")
    
def view_students():
    students = load_students()

    for student in students:
        print("ID:", student["id"])
        print("Name:", student["Name"])
        print("Age:", student["age"])
        print("School:", student["school"])
        print("----------------")       

def update_student():
    students = load_students()

    student_id = int(input("Enter student ID to update: "))

    for student in students:
        if student["id"] == student_id:
            new_name = input("Enter new name : ")
            new_age = int(input("Enter new age: "))

            student["Name"] = new_name
            student["age"] = new_age

            save_students(students)
            print("Student updated successfully!")
            return

    print("Student not found!")


def delete_student():
    students = load_students()

    student_id = int(input("Enter student ID to delete: "))

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

    choice = input("Choose search option: ")
    
    if choice == "1":
        student_id = int(input("Enter student ID: "))

        for student in students:
            if student["id"] == student_id:
                print("ID:", student["id"])
                print("Name:", student["Name"])
                print("Age:", student["age"])
                print("School:", student["school"])
                return

        print("Student not found!")
        
    elif choice == "2":
        name = input("Enter student name: ")

        for student in students:
            if student["Name"].lower() == name.lower():
                print("ID:", student["id"])
                print("Name:", student["Name"])
                print("Age:", student["age"])
                print("School:", student["school"])
                return

        print("Student not found!")        
        
    elif choice == "3":
        school = input("Enter school: ")
        found = False

        for student in students:
            if student["school"].lower() == school.lower():
                print("ID:", student["id"])
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

    choice = input("Choose an option: ")

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