import sqlite3
import json
from datetime import datetime
import os


# ============================================================
# DATABASE SETUP
# ============================================================

DB_NAME = "bank_debt_manager.db"


def connect_db():
    return sqlite3.connect(DB_NAME)


def create_database():
    conn = connect_db()
    cursor = conn.cursor()

    # Money YOU owe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            amount_owed REAL NOT NULL,
            created_date TEXT NOT NULL
        )
    """)

    # Payments for money YOU owe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            debt_id INTEGER NOT NULL,
            amount_paid REAL NOT NULL,
            payment_date TEXT NOT NULL,
            note TEXT,
            FOREIGN KEY (debt_id) REFERENCES debts(id)
        )
    """)

    # Money people owe YOU
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS money_owned_to_me (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT NOT NULL,
            amount_owned REAL NOT NULL,
            created_date TEXT NOT NULL
        )
    """)

    # Payments received from people
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS money_owned_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            money_owned_id INTEGER NOT NULL,
            amount_paid REAL NOT NULL,
            payment_date TEXT NOT NULL,
            note TEXT,
            FOREIGN KEY (money_owned_id)
            REFERENCES money_owned_to_me(id)
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# INPUT VALIDATION
# ============================================================

def get_amount(message):
    while True:
        try:
            amount = float(input(message))

            if amount < 0:
                print("Amount cannot be negative.")
                continue

            return amount

        except ValueError:
            print("Please enter a valid number.")


def get_date():
    while True:
        date = input(
            "Enter date (YYYY-MM-DD), "
            "or press Enter for today: "
        ).strip()

        if date == "":
            return datetime.now().strftime("%Y-%m-%d")

        try:
            datetime.strptime(date, "%Y-%m-%d")
            return date
        except ValueError:
            print("Invalid date format.")


# ============================================================
# ADD NEW DEBT - MONEY YOU OWE
# ============================================================

def add_debt():
    print("\n===== ADD NEW DEBT =====")

    name = input("Enter person's name: ").strip()

    if not name:
        print("Name cannot be empty.")
        return

    bank = input("Enter bank name: ").strip()

    if not bank:
        print("Bank name cannot be empty.")
        return

    amount = get_amount("Enter amount owed: ₦")

    if amount <= 0:
        print("Amount must be greater than zero.")
        return

    date = datetime.now().strftime("%Y-%m-%d")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO debts
        (person_name, bank_name, amount_owed, created_date)
        VALUES (?, ?, ?, ?)
    """, (name, bank, amount, date))

    conn.commit()
    conn.close()

    print("\nDebt added successfully.")


# ============================================================
# ADD MORE TO EXISTING DEBT - MONEY YOU OWE
# ============================================================

def add_to_existing_debt():
    print("\n===== ADD TO EXISTING DEBT =====")

    # Show existing debts first
    view_debts()

    debt_id = input(
        "\nEnter Debt ID to add more money to: "
    ).strip()

    if not debt_id.isdigit():
        print("Invalid ID.")
        return

    debt_id = int(debt_id)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT person_name,
               bank_name,
               amount_owed
        FROM debts
        WHERE id = ?
    """, (debt_id,))

    debt = cursor.fetchone()

    if not debt:
        print("Debt not found.")
        conn.close()
        return

    person_name, bank_name, current_debt = debt

    print("\n--------------------------------")
    print("Person:", person_name)
    print("Bank:", bank_name)
    print(f"Current Total Debt: ₦{current_debt:,.2f}")
    print("--------------------------------")

    additional_amount = get_amount(
        "Enter additional debt amount: ₦"
    )

    if additional_amount <= 0:
        print("Amount must be greater than zero.")
        conn.close()
        return

    new_total = current_debt + additional_amount

    cursor.execute("""
        UPDATE debts
        SET amount_owed = ?
        WHERE id = ?
    """, (new_total, debt_id))

    conn.commit()
    conn.close()

    print("\n================================")
    print("       DEBT UPDATED")
    print("================================")
    print(f"Previous Debt: ₦{current_debt:,.2f}")
    print(f"Additional Debt: ₦{additional_amount:,.2f}")
    print(f"New Total Debt: ₦{new_total:,.2f}")
    print("================================")


# ============================================================
# GET TOTAL PAID
# ============================================================

def get_total_paid(debt_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount_paid), 0)
        FROM payments
        WHERE debt_id = ?
    """, (debt_id,))

    total = cursor.fetchone()[0]

    conn.close()

    return total


# ============================================================
# ADD PAYMENT TO A DEBT
# ============================================================

def add_payment():
    print("\n===== RECORD NEW PAYMENT =====")

    debt_id = input("Enter Debt ID: ").strip()

    if not debt_id.isdigit():
        print("Invalid ID format.")
        return

    debt_id = int(debt_id)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT amount_owed,
               person_name,
               bank_name
        FROM debts
        WHERE id = ?
    """, (debt_id,))

    debt = cursor.fetchone()

    if not debt:
        print("Debt not found.")
        conn.close()
        return

    amount_owed, person_name, bank_name = debt

    cursor.execute("""
        SELECT COALESCE(SUM(amount_paid), 0)
        FROM payments
        WHERE debt_id = ?
    """, (debt_id,))

    total_paid = cursor.fetchone()[0]

    remaining = amount_owed - total_paid

    if remaining <= 0:
        print("This debt is already fully paid.")
        conn.close()
        return

    print("\n--------------------------------")
    print("Person:", person_name)
    print("Bank:", bank_name)
    print(f"Total Debt: ₦{amount_owed:,.2f}")
    print(f"Total Paid: ₦{total_paid:,.2f}")
    print(f"Remaining: ₦{remaining:,.2f}")
    print("--------------------------------")

    payment = get_amount(
        "Enter payment amount: ₦"
    )

    if payment <= 0:
        print("Payment must be greater than zero.")
        conn.close()
        return

    if payment > remaining:
        print(
            f"Payment cannot exceed "
            f"₦{remaining:,.2f}."
        )
        conn.close()
        return

    payment_date = get_date()

    note = input(
        "Enter optional note: "
    ).strip()

    if not note:
        note = "Payment"

    cursor.execute("""
        INSERT INTO payments
        (debt_id, amount_paid,
         payment_date, note)
        VALUES (?, ?, ?, ?)
    """, (
        debt_id,
        payment,
        payment_date,
        note
    ))

    conn.commit()
    conn.close()

    new_total_paid = total_paid + payment
    new_remaining = amount_owed - new_total_paid

    print("\n================================")
    print("       PAYMENT SUCCESSFUL")
    print("================================")
    print(f"Payment: ₦{payment:,.2f}")
    print(f"Total Paid: ₦{new_total_paid:,.2f}")
    print(f"Remaining: ₦{new_remaining:,.2f}")

    if new_remaining <= 0:
        print("Status: FULLY PAID")
    else:
        print("Status: NOT FULLY PAID")

    print("================================")


# ============================================================
# VIEW ALL DEBTS
# ============================================================

def view_debts():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               person_name,
               bank_name,
               amount_owed,
               created_date
        FROM debts
        ORDER BY id DESC
    """)

    debts = cursor.fetchall()

    conn.close()

    print("\n================ ALL DEBTS ================")

    if not debts:
        print("No debts found.")
        return

    print(
        f"{'ID':<5}"
        f"{'Name':<20}"
        f"{'Bank':<20}"
        f"{'Owed':<15}"
        f"{'Paid':<15}"
        f"{'Remaining':<15}"
    )

    print("-" * 90)

    for debt in debts:

        debt_id, name, bank, owed, created = debt

        paid = get_total_paid(debt_id)
        remaining = owed - paid

        print(
            f"{debt_id:<5}"
            f"{name[:18]:<20}"
            f"{bank[:18]:<20}"
            f"₦{owed:<13,.2f}"
            f"₦{paid:<13,.2f}"
            f"₦{remaining:<13,.2f}"
        )


# ============================================================
# VIEW ONE DEBT
# ============================================================

def view_debt_details():
    print("\n===== DEBT DETAILS =====")

    debt_id = input("Enter debt ID: ").strip()

    if not debt_id.isdigit():
        print("Invalid ID.")
        return

    debt_id = int(debt_id)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT person_name,
               bank_name,
               amount_owed,
               created_date
        FROM debts
        WHERE id = ?
    """, (debt_id,))

    debt = cursor.fetchone()

    if debt is None:
        conn.close()
        print("Debt not found.")
        return

    name, bank, owed, created = debt

    cursor.execute("""
        SELECT id,
               amount_paid,
               payment_date,
               note
        FROM payments
        WHERE debt_id = ?
        ORDER BY payment_date
    """, (debt_id,))

    payments = cursor.fetchall()

    conn.close()

    total_paid = sum(
        payment[1]
        for payment in payments
    )

    remaining = owed - total_paid

    print("\n================================")
    print("PERSON:", name)
    print("BANK:", bank)
    print(f"TOTAL OWED: ₦{owed:,.2f}")
    print(f"TOTAL PAID: ₦{total_paid:,.2f}")
    print(f"REMAINING: ₦{remaining:,.2f}")
    print("DATE CREATED:", created)

    if remaining <= 0:
        print("STATUS: FULLY PAID")
    else:
        print("STATUS: NOT FULLY PAID")

    print("================================")

    print("\n----- PAYMENT HISTORY -----")

    if not payments:
        print("No payments recorded.")
        return

    for payment in payments:

        payment_id, amount, date, note = payment

        print(
            f"Payment ID: {payment_id} | "
            f"₦{amount:,.2f} | "
            f"{date}"
        )

        if note:
            print("Note:", note)


# ============================================================
# SEARCH DEBT
# ============================================================

def search_debt():
    print("\n===== SEARCH DEBT =====")

    search = input(
        "Enter person's name or bank name: "
    ).strip()

    if not search:
        print("Search cannot be empty.")
        return

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               person_name,
               bank_name,
               amount_owed
        FROM debts
        WHERE person_name LIKE ?
        OR bank_name LIKE ?
        ORDER BY id DESC
    """, (
        f"%{search}%",
        f"%{search}%"
    ))

    results = cursor.fetchall()

    conn.close()

    if not results:
        print("No matching debt found.")
        return

    print("\n===== SEARCH RESULTS =====")

    for debt in results:

        debt_id, name, bank, owed = debt

        paid = get_total_paid(debt_id)
        remaining = owed - paid

        print("\n----------------------------")
        print("ID:", debt_id)
        print("Name:", name)
        print("Bank:", bank)
        print(f"Owed: ₦{owed:,.2f}")
        print(f"Paid: ₦{paid:,.2f}")
        print(f"Remaining: ₦{remaining:,.2f}")


# ============================================================
# DELETE DEBT
# ============================================================

def delete_debt():
    print("\n===== DELETE DEBT =====")

    view_debts()

    debt_id = input(
        "\nEnter debt ID to delete: "
    ).strip()

    if not debt_id.isdigit():
        print("Invalid ID.")
        return

    debt_id = int(debt_id)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT person_name "
        "FROM debts WHERE id = ?",
        (debt_id,)
    )

    debt = cursor.fetchone()

    if not debt:
        print("Debt not found.")
        conn.close()
        return

    print("Debt belongs to:", debt[0])

    confirm = input(
        "Are you sure? (yes/no): "
    ).strip().lower()

    if confirm != "yes":
        print("Deletion cancelled.")
        conn.close()
        return

    cursor.execute(
        "DELETE FROM payments "
        "WHERE debt_id = ?",
        (debt_id,)
    )

    cursor.execute(
        "DELETE FROM debts "
        "WHERE id = ?",
        (debt_id,)
    )

    conn.commit()
    conn.close()

    print("Debt deleted successfully.")


# ============================================================
# ADD MONEY OWED TO YOU
# ============================================================

def add_money_owned_to_me():
    print("\n===== ADD MONEY OWED TO ME =====")

    person_name = input(
        "Enter person's name: "
    ).strip()

    if not person_name:
        print("Name cannot be empty.")
        return

    amount_owned = get_amount(
        "Enter amount this person owes you: ₦"
    )

    if amount_owned <= 0:
        print("Amount must be greater than zero.")
        return

    date = datetime.now().strftime("%Y-%m-%d")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO money_owned_to_me
        (person_name, amount_owned, created_date)
        VALUES (?, ?, ?)
    """, (
        person_name,
        amount_owned,
        date
    ))

    conn.commit()
    conn.close()

    print("\nMoney owed to you added successfully.")


# ============================================================
# ADD MORE TO EXISTING MONEY OWED TO YOU
# ============================================================

def add_to_existing_money_owned():
    print("\n===== ADD TO EXISTING MONEY OWED TO ME =====")

    view_money_owned_to_me()

    money_id = input(
        "\nEnter ID to add more money to: "
    ).strip()

    if not money_id.isdigit():
        print("Invalid ID.")
        return

    money_id = int(money_id)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT person_name,
               amount_owned
        FROM money_owned_to_me
        WHERE id = ?
    """, (money_id,))

    record = cursor.fetchone()

    if not record:
        print("Record not found.")
        conn.close()
        return

    person_name, current_amount = record

    print("\n--------------------------------")
    print("Person:", person_name)
    print(
        f"Current Amount Owed: "
        f"₦{current_amount:,.2f}"
    )
    print("--------------------------------")

    additional_amount = get_amount(
        "Enter additional amount owed: ₦"
    )

    if additional_amount <= 0:
        print("Amount must be greater than zero.")
        conn.close()
        return

    new_total = current_amount + additional_amount

    cursor.execute("""
        UPDATE money_owned_to_me
        SET amount_owned = ?
        WHERE id = ?
    """, (
        new_total,
        money_id
    ))

    conn.commit()
    conn.close()

    print("\n================================")
    print("       RECORD UPDATED")
    print("================================")
    print(
        f"Previous Amount: "
        f"₦{current_amount:,.2f}"
    )
    print(
        f"Additional Amount: "
        f"₦{additional_amount:,.2f}"
    )
    print(
        f"New Total Owed: "
        f"₦{new_total:,.2f}"
    )
    print("================================")


# ============================================================
# GET TOTAL RECEIVED
# ============================================================

def get_total_received(money_owned_id):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount_paid), 0)
        FROM money_owned_payments
        WHERE money_owned_id = ?
    """, (money_owned_id,))

    total = cursor.fetchone()[0]

    conn.close()

    return total


# ============================================================
# VIEW MONEY OWED TO YOU
# ============================================================

def view_money_owned_to_me():

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               person_name,
               amount_owned,
               created_date
        FROM money_owned_to_me
        ORDER BY id DESC
    """)

    records = cursor.fetchall()

    conn.close()

    print("\n========== MONEY OWED TO YOU ==========")

    if not records:
        print("Nobody currently owes you money.")
        return

    print(
        f"{'ID':<5}"
        f"{'Name':<20}"
        f"{'Owed':<15}"
        f"{'Received':<15}"
        f"{'Remaining':<15}"
    )

    print("-" * 70)

    for record in records:

        money_id, name, owed, created = record

        received = get_total_received(
            money_id
        )

        remaining = owed - received

        print(
            f"{money_id:<5}"
            f"{name[:18]:<20}"
            f"₦{owed:<13,.2f}"
            f"₦{received:<13,.2f}"
            f"₦{remaining:<13,.2f}"
        )


# ============================================================
# RECEIVE PAYMENT FROM SOMEONE
# ============================================================

def receive_money_owned_payment():

    print("\n===== RECEIVE MONEY OWED TO YOU =====")

    view_money_owned_to_me()

    money_id = input(
        "\nEnter ID: "
    ).strip()

    if not money_id.isdigit():
        print("Invalid ID.")
        return

    money_id = int(money_id)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT person_name,
               amount_owned
        FROM money_owned_to_me
        WHERE id = ?
    """, (money_id,))

    record = cursor.fetchone()

    if not record:
        print("Record not found.")
        conn.close()
        return

    person_name, amount_owned = record

    cursor.execute("""
        SELECT COALESCE(SUM(amount_paid), 0)
        FROM money_owned_payments
        WHERE money_owned_id = ?
    """, (money_id,))

    total_received = cursor.fetchone()[0]

    remaining = amount_owned - total_received

    if remaining <= 0:
        print("This person has already fully paid.")
        conn.close()
        return

    print("\n--------------------------------")
    print("Person:", person_name)
    print(f"Total Owed: ₦{amount_owned:,.2f}")
    print(f"Received: ₦{total_received:,.2f}")
    print(f"Remaining: ₦{remaining:,.2f}")
    print("--------------------------------")

    payment = get_amount(
        "Enter amount received: ₦"
    )

    if payment <= 0:
        print("Payment must be greater than zero.")
        conn.close()
        return

    if payment > remaining:
        print(
            f"Payment cannot exceed "
            f"₦{remaining:,.2f}."
        )
        conn.close()
        return

    payment_date = get_date()

    note = input(
        "Enter optional note: "
    ).strip()

    if not note:
        note = "Payment received"

    cursor.execute("""
        INSERT INTO money_owned_payments
        (money_owned_id,
         amount_paid,
         payment_date,
         note)
        VALUES (?, ?, ?, ?)
    """, (
        money_id,
        payment,
        payment_date,
        note
    ))

    conn.commit()
    conn.close()

    new_total = total_received + payment
    new_remaining = amount_owned - new_total

    print("\n================================")
    print("       PAYMENT RECEIVED")
    print("================================")
    print(f"Received: ₦{payment:,.2f}")
    print(f"Total Received: ₦{new_total:,.2f}")
    print(f"Remaining: ₦{new_remaining:,.2f}")

    if new_remaining <= 0:
        print("Status: FULLY PAID")
    else:
        print("Status: NOT FULLY PAID")

    print("================================")


# ============================================================
# VIEW MONEY OWED DETAILS
# ============================================================

def view_money_owned_details():

    print("\n===== MONEY OWED TO YOU DETAILS =====")

    money_id = input("Enter ID: ").strip()

    if not money_id.isdigit():
        print("Invalid ID.")
        return

    money_id = int(money_id)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT person_name,
               amount_owned,
               created_date
        FROM money_owned_to_me
        WHERE id = ?
    """, (money_id,))

    record = cursor.fetchone()

    if not record:
        print("Record not found.")
        conn.close()
        return

    person_name, amount_owned, created_date = record

    cursor.execute("""
        SELECT id,
               amount_paid,
               payment_date,
               note
        FROM money_owned_payments
        WHERE money_owned_id = ?
        ORDER BY payment_date
    """, (money_id,))

    payments = cursor.fetchall()

    conn.close()

    total_received = sum(
        payment[1]
        for payment in payments
    )

    remaining = amount_owned - total_received

    print("\n================================")
    print("PERSON:", person_name)
    print(f"TOTAL OWED: ₦{amount_owned:,.2f}")
    print(f"TOTAL RECEIVED: ₦{total_received:,.2f}")
    print(f"REMAINING: ₦{remaining:,.2f}")
    print("DATE CREATED:", created_date)

    if remaining <= 0:
        print("STATUS: FULLY PAID")
    else:
        print("STATUS: NOT FULLY PAID")

    print("================================")

    print("\n----- PAYMENT HISTORY -----")

    if not payments:
        print("No payments received.")
        return

    for payment in payments:

        payment_id, amount, date, note = payment

        print(
            f"Payment ID: {payment_id} | "
            f"₦{amount:,.2f} | "
            f"{date}"
        )

        if note:
            print("Note:", note)


# ============================================================
# SEARCH MONEY OWED TO YOU
# ============================================================

def search_money_owned():

    print("\n===== SEARCH MONEY OWED TO YOU =====")

    search = input(
        "Enter person's name: "
    ).strip()

    if not search:
        print("Search cannot be empty.")
        return

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               person_name,
               amount_owned
        FROM money_owned_to_me
        WHERE person_name LIKE ?
        ORDER BY id DESC
    """, (f"%{search}%",))

    results = cursor.fetchall()

    conn.close()

    if not results:
        print("No matching person found.")
        return

    for record in results:

        money_id, name, owed = record

        received = get_total_received(
            money_id
        )

        remaining = owed - received

        print("\n----------------------------")
        print("ID:", money_id)
        print("Name:", name)
        print(f"Owed: ₦{owed:,.2f}")
        print(f"Received: ₦{received:,.2f}")
        print(f"Remaining: ₦{remaining:,.2f}")


# ============================================================
# DELETE MONEY OWED TO YOU
# ============================================================

def delete_money_owned():

    print("\n===== DELETE MONEY OWED RECORD =====")

    view_money_owned_to_me()

    money_id = input(
        "\nEnter ID to delete: "
    ).strip()

    if not money_id.isdigit():
        print("Invalid ID.")
        return

    money_id = int(money_id)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT person_name
        FROM money_owned_to_me
        WHERE id = ?
    """, (money_id,))

    record = cursor.fetchone()

    if not record:
        print("Record not found.")
        conn.close()
        return

    print("Person:", record[0])

    confirm = input(
        "Are you sure? (yes/no): "
    ).strip().lower()

    if confirm != "yes":
        print("Deletion cancelled.")
        conn.close()
        return

    cursor.execute("""
        DELETE FROM money_owned_payments
        WHERE money_owned_id = ?
    """, (money_id,))

    cursor.execute("""
        DELETE FROM money_owned_to_me
        WHERE id = ?
    """, (money_id,))

    conn.commit()
    conn.close()

    print("Record deleted successfully.")


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

def show_summary():

    conn = connect_db()
    cursor = conn.cursor()

    # Money YOU owe
    cursor.execute("""
        SELECT COALESCE(SUM(amount_owed), 0)
        FROM debts
    """)

    total_owed = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(amount_paid), 0)
        FROM payments
    """)

    total_paid = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM debts
    """)

    number_of_debts = cursor.fetchone()[0]

    # Money owed TO YOU
    cursor.execute("""
        SELECT COALESCE(SUM(amount_owned), 0)
        FROM money_owned_to_me
    """)

    total_people_owe = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(amount_paid), 0)
        FROM money_owned_payments
    """)

    total_received = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM money_owned_to_me
    """)

    number_of_people_owe = cursor.fetchone()[0]

    conn.close()

    remaining_debt = total_owed - total_paid
    remaining_to_receive = (
        total_people_owe - total_received
    )

    print("\n==============================================")
    print("             FINANCIAL SUMMARY")
    print("==============================================")

    print("\n--- MONEY YOU OWE ---")
    print(f"Number of debts: {number_of_debts}")
    print(f"Total owed: ₦{total_owed:,.2f}")
    print(f"Total paid: ₦{total_paid:,.2f}")
    print(
        f"Remaining to pay: "
        f"₦{remaining_debt:,.2f}"
    )

    print("\n--- MONEY OWED TO YOU ---")
    print(
        f"People owing you: "
        f"{number_of_people_owe}"
    )
    print(
        f"Total owed to you: "
        f"₦{total_people_owe:,.2f}"
    )
    print(
        f"Total received: "
        f"₦{total_received:,.2f}"
    )
    print(
        f"Remaining to receive: "
        f"₦{remaining_to_receive:,.2f}"
    )

    print("\n==============================================")


# ============================================================
# EXPORT JSON BACKUP
# ============================================================

def export_json():

    conn = connect_db()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Export debts
    # --------------------------------------------------------

    cursor.execute("""
        SELECT id,
               person_name,
               bank_name,
               amount_owed,
               created_date
        FROM debts
    """)

    debts = cursor.fetchall()

    debt_data = []

    for debt in debts:

        debt_id, name, bank, owed, created = debt

        cursor.execute("""
            SELECT amount_paid,
                   payment_date,
                   note
            FROM payments
            WHERE debt_id = ?
        """, (debt_id,))

        payments = cursor.fetchall()

        debt_data.append({
            "id": debt_id,
            "name": name,
            "bank": bank,
            "amount_owed": owed,
            "created_date": created,
            "payments": [
                {
                    "amount": payment[0],
                    "date": payment[1],
                    "note": payment[2]
                }
                for payment in payments
            ]
        })

    # --------------------------------------------------------
    # Export money owed to you
    # --------------------------------------------------------

    cursor.execute("""
        SELECT id,
               person_name,
               amount_owned,
               created_date
        FROM money_owned_to_me
    """)

    records = cursor.fetchall()

    money_data = []

    for record in records:

        money_id, name, amount, created = record

        cursor.execute("""
            SELECT amount_paid,
                   payment_date,
                   note
            FROM money_owned_payments
            WHERE money_owned_id = ?
        """, (money_id,))

        payments = cursor.fetchall()

        money_data.append({
            "id": money_id,
            "name": name,
            "amount_owned": amount,
            "created_date": created,
            "payments": [
                {
                    "amount": payment[0],
                    "date": payment[1],
                    "note": payment[2]
                }
                for payment in payments
            ]
        })

    conn.close()

    data = {
        "debts": debt_data,
        "money_owned_to_me": money_data,
        "backup_date": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    filename = "bank_debt_backup.json"

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"\nBackup created successfully: "
        f"{filename}"
    )


# ============================================================
# IMPORT JSON BACKUP
# ============================================================

def import_json():

    filename = "bank_debt_backup.json"

    if not os.path.exists(filename):
        print("Backup file not found.")
        return

    confirm = input(
        "Import backup? Existing data will remain. "
        "(yes/no): "
    ).strip().lower()

    if confirm != "yes":
        print("Import cancelled.")
        return

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

    except json.JSONDecodeError:

        print("Backup file is not valid JSON.")
        return

    conn = connect_db()
    cursor = conn.cursor()

    # Import debts
    for debt in data.get("debts", []):

        cursor.execute("""
            INSERT INTO debts
            (person_name,
             bank_name,
             amount_owed,
             created_date)
            VALUES (?, ?, ?, ?)
        """, (
            debt["name"],
            debt["bank"],
            debt["amount_owed"],
            debt["created_date"]
        ))

        new_debt_id = cursor.lastrowid

        for payment in debt.get(
            "payments", []
        ):

            cursor.execute("""
                INSERT INTO payments
                (debt_id,
                 amount_paid,
                 payment_date,
                 note)
                VALUES (?, ?, ?, ?)
            """, (
                new_debt_id,
                payment["amount"],
                payment["date"],
                payment.get("note", "")
            ))

    # Import money owed to you
    for record in data.get(
        "money_owned_to_me",
        []
    ):

        cursor.execute("""
            INSERT INTO money_owned_to_me
            (person_name,
             amount_owned,
             created_date)
            VALUES (?, ?, ?)
        """, (
            record["name"],
            record["amount_owned"],
            record["created_date"]
        ))

        new_money_id = cursor.lastrowid

        for payment in record.get(
            "payments", []
        ):

            cursor.execute("""
                INSERT INTO money_owned_payments
                (money_owned_id,
                 amount_paid,
                 payment_date,
                 note)
                VALUES (?, ?, ?, ?)
            """, (
                new_money_id,
                payment["amount"],
                payment["date"],
                payment.get("note", "")
            ))

    conn.commit()
    conn.close()

    print("Backup imported successfully.")


# ============================================================
# MONEY OWED TO ME MENU
# ============================================================

def money_owned_menu():

    while True:

        print("\n======================================")
        print("          MONEY OWED TO ME")
        print("======================================")
        print("1. Add person who owes me")
        print("2. Add to existing debt")
        print("3. View all people who owe me")
        print("4. View payment details")
        print("5. Receive payment")
        print("6. Search person")
        print("7. Delete record")
        print("0. Back to main menu")
        print("======================================")

        choice = input(
            "Choose an option: "
        ).strip()

        if choice == "1":
            add_money_owned_to_me()

        elif choice == "2":
            add_to_existing_money_owned()

        elif choice == "3":
            view_money_owned_to_me()

        elif choice == "4":
            view_money_owned_details()

        elif choice == "5":
            receive_money_owned_payment()

        elif choice == "6":
            search_money_owned()

        elif choice == "7":
            delete_money_owned()

        elif choice == "0":
            break

        else:
            print("Invalid option.")


# ============================================================
# MAIN MENU
# ============================================================

def main():

    create_database()

    while True:

        print("\n")
        print("======================================")
        print("          BANK DEBT MANAGER")
        print("======================================")
        print("1. Add new debt")
        print("2. Add to existing debt")
        print("3. View all debts")
        print("4. View debt details")
        print("5. Make a payment")
        print("6. Search debt")
        print("7. Financial summary")
        print("8. Delete debt")
        print("9. Export JSON backup")
        print("10. Import JSON backup")
        print("11. Money owed to me")
        print("0. Exit")
        print("======================================")

        choice = input(
            "Choose an option: "
        ).strip()

        if choice == "1":
            add_debt()

        elif choice == "2":
            add_to_existing_debt()

        elif choice == "3":
            view_debts()

        elif choice == "4":
            view_debt_details()

        elif choice == "5":
            add_payment()

        elif choice == "6":
            search_debt()

        elif choice == "7":
            show_summary()

        elif choice == "8":
            delete_debt()

        elif choice == "9":
            export_json()

        elif choice == "10":
            import_json()

        elif choice == "11":
            money_owned_menu()

        elif choice == "0":
            print(
                "\nThank you for using "
                "Bank Debt Manager."
            )
            break

        else:
            print(
                "Invalid option. "
                "Please choose again."
            )


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":
    main()