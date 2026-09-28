import json


def load_names():
    try:
        with open("names.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def suggest_names(name, names):
    suggestions = []

    number = 1

    while len(suggestions) < 3:
        new_name = name + str(number)

        if new_name not in names:
            suggestions.append(new_name)

        number += 1

    return suggestions

def choose_name(name, names):
    if name in names:
        print(f"{name} is already being used.")

        suggestion = name + "1"
        print(f"Suggested name: {suggestion}")

        new_name = input("Or enter your own name: ")

        if new_name in names:
            print(f"{new_name} is also already being used.")
            return None

        return new_name

    return name



def register_name():
    names = load_names()

    name = input("Enter your name: ")

    if name in names:
        suggestion = choose_name(name, name)

        print(f"{name} is already being used.")
        print(f"You can use: {suggestion}")

    else:
        names.append(name)

        with open("names.json", "w") as file:
            json.dump(names, file, indent=4)

        print(f"{name} has been saved successfully.")


register_name()