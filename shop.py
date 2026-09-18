import csv
from datetime import datetime
import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

DB_NAME = "shop.db"


def connect_db():
    return sqlite3.connect(DB_NAME)


def create_tables():
    connection = connect_db()
    cursor = connection.cursor()

    # Create products table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            buying_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            minimum_stock INTEGER NOT NULL,
            date_added TEXT NOT NULL
        )
    """
    )

    # Create sales table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity_sold INTEGER NOT NULL,
            selling_price REAL NOT NULL,
            total REAL NOT NULL,
            sale_date TEXT NOT NULL,
            receipt_no TEXT,
            buying_price REAL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """
    )

    # Create expenses table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            expense_date TEXT NOT NULL
        )
    """
    )

    connection.commit()
    connection.close()


# === ITEM MANAGEMENT ===


def add_item():
    print("\n===== ADD NEW ITEM =====")
    name = input("Enter item name: ").strip()
    category = input("Enter category: ").strip()
    buying_price = float(input("Enter buying price: "))
    selling_price = float(input("Enter selling price: "))
    quantity = int(input("Enter quantity: "))
    minimum_stock = int(input("Enter minimum stock: "))
    date_added = input("Enter date (YYYY-MM-DD): ").strip()

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO products
        (name, category, buying_price, selling_price, quantity, minimum_stock, date_added)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            name,
            category,
            buying_price,
            selling_price,
            quantity,
            minimum_stock,
            date_added,
        ),
    )

    connection.commit()
    connection.close()
    print("\nItem added successfully!")


def view_items():
    print("\n===== ALL SHOP ITEMS =====")
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, name, category, buying_price, selling_price, quantity, date_added
        FROM products
    """
    )

    items = cursor.fetchall()
    connection.close()

    if not items:
        print("No items found.")
        return

    for item in items:
        print("--------------------------------")
        print(f"ID: {item[0]}")
        print(f"Name: {item[1]}")
        print(f"Category: {item[2]}")
        print(f"Buying Price: ₦{item[3]:,.2f}")
        print(f"Selling Price: ₦{item[4]:,.2f}")
        print(f"Quantity: {item[5]}")
        print(f"Date Added: {item[6]}")


def search_item():
    print("\n===== SEARCH ITEM =====")
    search = input("Enter item name: ").strip()

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, name, category, buying_price, selling_price, quantity, date_added
        FROM products
        WHERE name LIKE ?
    """,
        (f"%{search}%",),
    )

    items = cursor.fetchall()
    connection.close()

    if not items:
        print("No item found.")
        return

    for item in items:
        print("--------------------------------")
        print(f"ID: {item[0]}")
        print(f"Name: {item[1]}")
        print(f"Category: {item[2]}")
        print(f"Buying Price: ₦{item[3]:,.2f}")
        print(f"Selling Price: ₦{item[4]:,.2f}")
        print(f"Quantity: {item[5]}")
        print(f"Date Added: {item[6]}")


def edit_item():
    print("\n===== EDIT ITEM =====")
    item_id = int(input("Enter item ID: "))

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM products WHERE id = ?", (item_id,))
    item = cursor.fetchone()

    if not item:
        print("Item not found.")
        connection.close()
        return

    print(f"\nCurrent item: {item[1]}")
    print("Leave a field empty to keep the current value.")

    name = input(f"Name [{item[1]}]: ").strip()
    category = input(f"Category [{item[2]}]: ").strip()
    buying_price = input(f"Buying price [{item[3]}]: ").strip()
    selling_price = input(f"Selling price [{item[4]}]: ").strip()
    minimum_stock = input(f"Minimum stock [{item[6]}]: ").strip()

    name = name if name else item[1]
    category = category if category else item[2]
    buying_price = float(buying_price) if buying_price else item[3]
    selling_price = float(selling_price) if selling_price else item[4]
    minimum_stock = int(minimum_stock) if minimum_stock else item[6]

    cursor.execute(
        """
        UPDATE products
        SET name = ?, category = ?, buying_price = ?, selling_price = ?, minimum_stock = ?
        WHERE id = ?
    """,
        (name, category, buying_price, selling_price, minimum_stock, item_id),
    )

    connection.commit()
    connection.close()
    print("\nItem updated successfully!")


def delete_item():
    print("\n===== DELETE ITEM =====")
    item_id = int(input("Enter item ID to delete: "))

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT name FROM products WHERE id = ?", (item_id,))
    item = cursor.fetchone()

    if not item:
        print("Item not found.")
        connection.close()
        return

    print(f"Item found: {item[0]}")
    confirm = input("Are you sure you want to delete it? (yes/no): ").lower()

    if confirm == "yes":
        cursor.execute("DELETE FROM products WHERE id = ?", (item_id,))
        connection.commit()
        print("Item deleted successfully!")
    else:
        print("Delete cancelled.")

    connection.close()


# === STOCK MANAGEMENT ===


def add_stock():
    print("\n===== ADD MORE STOCK =====")
    item_id = int(input("Enter item ID: "))
    amount = int(input("Enter quantity to add: "))

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT name, quantity FROM products WHERE id = ?", (item_id,)
    )
    item = cursor.fetchone()

    if not item:
        print("Item not found.")
        connection.close()
        return

    new_quantity = item[1] + amount
    cursor.execute(
        "UPDATE products SET quantity = ? WHERE id = ?", (new_quantity, item_id)
    )

    connection.commit()
    connection.close()

    print("\nStock added successfully!")
    print(f"Item: {item[0]}")
    print(f"Old quantity: {item[1]}")
    print(f"New quantity: {new_quantity}")


def remove_stock():
    print("\n===== REMOVE STOCK =====")
    item_id = int(input("Enter item ID: "))
    amount = int(input("Enter quantity to remove: "))

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT name, quantity FROM products WHERE id = ?", (item_id,)
    )
    item = cursor.fetchone()

    if not item:
        print("Item not found.")
        connection.close()
        return

    if amount > item[1]:
        print("You cannot remove more stock than you have.")
        connection.close()
        return

    new_quantity = item[1] - amount
    cursor.execute(
        "UPDATE products SET quantity = ? WHERE id = ?", (new_quantity, item_id)
    )

    connection.commit()
    connection.close()

    print("\nStock removed successfully!")
    print(f"Item: {item[0]}")
    print(f"Old quantity: {item[1]}")
    print(f"New quantity: {new_quantity}")


def low_stock():
    print("\n===== LOW STOCK ITEMS =====")
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, quantity, minimum_stock
        FROM products
        WHERE quantity <= minimum_stock
    """)

    items = cursor.fetchall()
    connection.close()

    if not items:
        print("No low-stock items.")
        return

    for item in items:
        print("--------------------------------")
        print(f"ID: {item[0]}")
        print(f"Name: {item[1]}")
        print(f"Current Quantity: {item[2]}")
        print(f"Minimum Stock: {item[3]}")
        print("⚠️ LOW STOCK - RESTOCK NEEDED")


# === SALES MANAGEMENT ===


def sell_item():
    print("\n===== SELL ITEM =====")

    item_id = int(input("Enter item ID: "))
    quantity_sold = int(input("Enter quantity sold: "))

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT name, selling_price, quantity, buying_price
        FROM products
        WHERE id = ?
    """,
        (item_id,),
    )

    item = cursor.fetchone()

    if not item:
        print("Item not found.")
        connection.close()
        return

    if quantity_sold <= 0:
        print("Quantity must be greater than zero.")
        connection.close()
        return

    if quantity_sold > item[2]:
        print("Not enough stock available.")
        connection.close()
        return

    total = quantity_sold * item[1]
    new_quantity = item[2] - quantity_sold

    receipt_no = datetime.now().strftime("%Y%m%d%H%M%S")
    sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        UPDATE products
        SET quantity = ?
        WHERE id = ?
    """,
        (new_quantity, item_id),
    )

    cursor.execute(
        """
        INSERT INTO sales
        (product_id, quantity_sold, selling_price,
         total, sale_date, receipt_no, buying_price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            item_id,
            quantity_sold,
            item[1],
            total,
            sale_date,
            receipt_no,
            item[3],
        ),
    )

    connection.commit()
    connection.close()


def print_receipt(receipt_no, item_name, quantity, price, total, sale_date):
    print("\n================================")
    print("           MY SHOP")
    print("           RECEIPT")
    print("================================")

    print(f"Receipt No: {receipt_no}")
    print(f"Item: {item_name}")
    print(f"Quantity: {quantity}")
    print(f"Price: ₦{price:,.2f}")
    print("--------------------------------")
    print(f"TOTAL: ₦{total:,.2f}")
    print(f"Date: {sale_date}")

    print("================================")
    print("        Thank you!")
    print("================================")


def sell_multiple_items():
    print("\n===== NEW CUSTOMER SALE =====")

    receipt_no = datetime.now().strftime("%Y%m%d%H%M%S")
    items_bought = []
    grand_total = 0

    while True:
        item_id = int(input("Enter item ID (0 to finish): "))

        if item_id == 0:
            break

        quantity = int(input("Enter quantity: "))

        if quantity <= 0:
            print("Quantity must be greater than zero.")
            continue

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name, selling_price, quantity, buying_price
            FROM products
            WHERE id = ?
        """,
            (item_id,),
        )

        item = cursor.fetchone()

        if not item:
            print("Item not found.")
            connection.close()
            continue

        if quantity > item[2]:
            print("Not enough stock available.")
            connection.close()
            continue

        total = quantity * item[1]
        new_quantity = item[2] - quantity

        sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            UPDATE products
            SET quantity = ?
            WHERE id = ?
        """,
            (new_quantity, item_id),
        )

        cursor.execute(
            """
            INSERT INTO sales
            (product_id, quantity_sold, selling_price,
             total, sale_date, receipt_no, buying_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                item_id,
                quantity,
                item[1],
                total,
                sale_date,
                receipt_no,
                item[3],
            ),
        )

        connection.commit()
        connection.close()

        items_bought.append((item[0], quantity, item[1], item[3], total))

        grand_total += total

        print(f"{item[0]} added to receipt.")

    if not items_bought:
        print("No items were sold.")
        return

    print("\n================================")
    print("           MY SHOP")
    print("           RECEIPT")
    print("================================")
    print(f"Receipt No: {receipt_no}")

    for item in items_bought:
        print("--------------------------------")
        print(f"Item: {item[0]}")
        print(f"Quantity: {item[1]}")
        print(f"Selling Price: ₦{item[2]:,.2f}")
        print(f"Total: ₦{item[4]:,.2f}")

    print("--------------------------------")
    print(f"GRAND TOTAL: ₦{grand_total:,.2f}")
    print("================================")
    print("        Thank you!")
    print("================================")


def view_sales():
    print("\n===== SALES HISTORY =====")
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT sales.sale_id,
               products.name,
               sales.quantity_sold,
               sales.selling_price,
               sales.total,
               sales.sale_date,
               sales.receipt_no
        FROM sales
        JOIN products ON sales.product_id = products.id
        ORDER BY sales.sale_id DESC
    """)

    sales = cursor.fetchall()
    connection.close()

    if not sales:
        print("No sales found.")
        return

    for sale in sales:
        print("--------------------------------")
        print(f"Sale ID: {sale[0]}")
        print(f"Item: {sale[1]}")
        print(f"Quantity Sold: {sale[2]}")
        print(f"Selling Price: ₦{sale[3]:,.2f}")
        print(f"Total: ₦{sale[4]:,.2f}")
        print(f"Date: {sale[5]}")
        print(f"Receipt No: {sale[6]}")


def search_sales():
    print("\n===== SEARCH SALES =====")
    search = input("Enter item name: ").strip()

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT sales.sale_id,
               products.name,
               sales.quantity_sold,
               sales.selling_price,
               sales.total,
               sales.sale_date,
               sales.receipt_no
        FROM sales
        JOIN products ON sales.product_id = products.id
        WHERE products.name LIKE ?
        ORDER BY sales.sale_id DESC
    """,
        (f"%{search}%",),
    )

    sales = cursor.fetchall()
    connection.close()

    if not sales:
        print("No sales found.")
        return

    for sale in sales:
        print("--------------------------------")
        print(f"Sale ID: {sale[0]}")
        print(f"Item: {sale[1]}")
        print(f"Quantity Sold: {sale[2]}")
        print(f"Selling Price: ₦{sale[3]:,.2f}")
        print(f"Total: ₦{sale[4]:,.2f}")
        print(f"Date: {sale[5]}")
        print(f"Receipt No: {sale[6]}")


# === EXPENSE MANAGEMENT ===


def add_expense():
    print("\n===== ADD EXPENSE =====")
    description = input("Enter expense description: ").strip()
    amount = float(input("Enter amount: "))
    category = input("Enter category: ").strip()
    expense_date = input("Enter date (YYYY-MM-DD): ").strip()

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO expenses (description, amount, category, expense_date)
        VALUES (?, ?, ?, ?)
    """,
        (description, amount, category, expense_date),
    )

    connection.commit()
    connection.close()
    print("\nExpense added successfully!")


def view_expenses():
    print("\n===== EXPENSE HISTORY =====")
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT expense_id, description, amount, category, expense_date
        FROM expenses
        ORDER BY expense_id DESC
    """)

    expenses = cursor.fetchall()
    connection.close()

    if not expenses:
        print("No expenses found.")
        return

    for expense in expenses:
        print("--------------------------------")
        print(f"Expense ID: {expense[0]}")
        print(f"Description: {expense[1]}")
        print(f"Amount: ₦{expense[2]:,.2f}")
        print(f"Category: {expense[3]}")
        print(f"Date: {expense[4]}")


# === REPORTS & ANALYTICS ===


def show_financial_summary():
    print("\n===== FINANCIAL SUMMARY =====")
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT SUM(total) FROM sales")
    total_sales = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_expenses = cursor.fetchone()[0] or 0

    profit = total_sales - total_expenses
    connection.close()

    print(f"Total Sales: ₦{total_sales:,.2f}")
    print(f"Total Expenses: ₦{total_expenses:,.2f}")
    print("--------------------------------")
    print(f"Profit/Loss: ₦{profit:,.2f}")

    if profit > 0:
        print("Status: PROFIT")
    elif profit < 0:
        print("Status: LOSS")
    else:
        print("Status: BREAK-EVEN")


def show_product_profit():
    print("\n===== PRODUCT PROFIT =====")
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT products.name,
               SUM(sales.quantity_sold),
               SUM((sales.selling_price - products.buying_price) * sales.quantity_sold)
        FROM sales
        JOIN products ON sales.product_id = products.id
        GROUP BY products.id
    """)

    profits = cursor.fetchall()
    connection.close()

    if not profits:
        print("No sales found.")
        return

    total_profit = 0
    for profit in profits:
        print("--------------------------------")
        print(f"Item: {profit[0]}")
        print(f"Quantity Sold: {profit[1]}")
        print(f"Profit: ₦{profit[2]:,.2f}")
        total_profit += profit[2]

    print("--------------------------------")
    print(f"TOTAL PRODUCT PROFIT: ₦{total_profit:,.2f}")


def dashboard():
    print("\n================================")
    print("          SHOP DASHBOARD")
    print("================================")

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(quantity) FROM products")
    total_quantity = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(buying_price * quantity) FROM products")
    stock_value = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(total) FROM sales")
    total_sales = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_expenses = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT COUNT(*) FROM products WHERE quantity <= minimum_stock"
    )
    low_stock_count = cursor.fetchone()[0]

    profit = total_sales - total_expenses
    connection.close()

    print(f"Total Products: {total_products}")
    print(f"Total Quantity: {total_quantity}")
    print(f"Stock Value: ₦{stock_value:,.2f}")
    print(f"Total Sales: ₦{total_sales:,.2f}")
    print(f"Total Expenses: ₦{total_expenses:,.2f}")
    print(f"Profit/Loss: ₦{profit:,.2f}")
    print(f"Low Stock Items: {low_stock_count}")
    print("================================")


def daily_report():
    print("\n===== DAILY REPORT =====")
    report_date = input("Enter date (YYYY-MM-DD): ").strip()

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COALESCE(SUM(total), 0)
        FROM sales
        WHERE DATE(sale_date) = ?
    """,
        (report_date,),
    )
    total_sales = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE expense_date = ?
    """,
        (report_date,),
    )
    total_expenses = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COALESCE(SUM((sales.selling_price - products.buying_price) * sales.quantity_sold), 0)
        FROM sales
        JOIN products ON sales.product_id = products.id
        WHERE DATE(sale_date) = ?
    """,
        (report_date,),
    )
    product_profit = cursor.fetchone()[0]

    connection.close()
    net_result = product_profit - total_expenses

    print("\n================================")
    print(f"REPORT FOR: {report_date}")
    print("================================")
    print(f"Total Sales: ₦{total_sales:,.2f}")
    print(f"Product Profit: ₦{product_profit:,.2f}")
    print(f"Expenses: ₦{total_expenses:,.2f}")
    print("--------------------------------")
    print(f"Net Profit/Loss: ₦{net_result:,.2f}")
    print("================================")


def weekly_report():
    print("\n===== WEEKLY REPORT =====")
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM sales
        WHERE DATE(sale_date) >= DATE('now', '-6 days')
    """)
    total_sales = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM((sales.selling_price - products.buying_price) * sales.quantity_sold), 0)
        FROM sales
        JOIN products ON sales.product_id = products.id
        WHERE DATE(sale_date) >= DATE('now', '-6 days')
    """)
    product_profit = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE DATE(expense_date) >= DATE('now', '-6 days')
    """)
    total_expenses = cursor.fetchone()[0]

    connection.close()
    net_profit = product_profit - total_expenses

    print("\n================================")
    print("       LAST 7 DAYS")
    print("================================")
    print(f"Total Sales: ₦{total_sales:,.2f}")
    print(f"Product Profit: ₦{product_profit:,.2f}")
    print(f"Expenses: ₦{total_expenses:,.2f}")
    print("--------------------------------")
    print(f"Net Profit/Loss: ₦{net_profit:,.2f}")
    print("================================")


# === EXPORT & BACKUP ===


def backup_database():
    print("\n===== DATABASE BACKUP =====")
    if not os.path.exists(DB_NAME):
        print("Database file not found.")
        return

    backup_name = (
        "shop_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".db"
    )
    shutil.copy2(DB_NAME, backup_name)
    print("Backup created successfully!")
    print(f"Backup file: {backup_name}")


def export_products():
    print("\n===== EXPORT PRODUCTS =====")
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, category, buying_price, selling_price, quantity, minimum_stock, date_added
        FROM products
    """)

    products = cursor.fetchall()
    connection.close()

    filename = "products.csv"
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "ID",
            "Name",
            "Category",
            "Buying Price",
            "Selling Price",
            "Quantity",
            "Minimum Stock",
            "Date Added",
        ])
        writer.writerows(products)

    print(f"Products exported successfully to {filename}")


def export_sales():
    print("\n===== EXPORT SALES =====")
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT sales.sale_id,
               products.name,
               sales.quantity_sold,
               sales.selling_price,
               sales.total,
               sales.sale_date,
               sales.receipt_no
        FROM sales
        JOIN products
        ON sales.product_id = products.id
        ORDER BY sales.sale_id DESC
    """)

    sales = cursor.fetchall()
    connection.close()

    filename = "sales.csv"
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Sale ID",
            "Item",
            "Quantity Sold",
            "Selling Price",
            "Total",
            "Sale Date",
            "Receipt No",
        ])
        writer.writerows(sales)

    print(f"Sales exported successfully to {filename}")


def export_expenses():
    print("\n===== EXPORT EXPENSES =====")
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT expense_id, description, amount, category, expense_date
        FROM expenses
        ORDER BY expense_id DESC
    """)

    expenses = cursor.fetchall()
    connection.close()

    filename = "expenses.csv"
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["Expense ID", "Description", "Amount", "Category", "Date"]
        )
        writer.writerows(expenses)

    print(f"Expenses exported successfully to {filename}")


# === GUI SCREENS & DIALOGS ===


def inventory_screen(root, main_area):
    for widget in main_area.winfo_children():
        widget.destroy()

    heading = tk.Label(main_area, text="Inventory", font=("Arial", 24, "bold"))
    heading.pack(pady=20)

    button_frame = tk.Frame(main_area)
    button_frame.pack(pady=10)

    tk.Button(
        button_frame, text="Add Item", width=15, command=add_item_gui
    ).grid(row=0, column=0, padx=5)
    tk.Button(
        button_frame, text="Search Item", width=15, command=search_item
    ).grid(row=0, column=1, padx=5)
    tk.Button(
        button_frame, text="Edit Item", width=15, command=edit_item_gui
    ).grid(row=0, column=2, padx=5)
    tk.Button(
        button_frame, text="Delete Item", width=15, command=delete_item_gui
    ).grid(row=0, column=3, padx=5)

    tk.Button(
        button_frame, text="Add Stock", width=15, command=add_stock_gui
    ).grid(row=1, column=0, padx=5, pady=10)
    tk.Button(
        button_frame, text="Remove Stock", width=15, command=remove_stock_gui
    ).grid(row=1, column=1, padx=5, pady=10)
    tk.Button(
        button_frame, text="Low Stock", width=15, command=low_stock_gui
    ).grid(row=1, column=2, padx=5, pady=10)

    table_frame = tk.Frame(main_area)
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    columns = (
        "ID",
        "Name",
        "Category",
        "Buying Price",
        "Selling Price",
        "Quantity",
        "Minimum Stock",
        "Date",
    )
    table = ttk.Treeview(table_frame, columns=columns, show="headings")

    for column in columns:
        table.heading(column, text=column)
        table.column(column, width=100)

    table.pack(fill="both", expand=True)

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, name, category, buying_price, selling_price, quantity, minimum_stock, date_added
        FROM products
        ORDER BY id DESC
    """)
    products = cursor.fetchall()
    connection.close()

    for product in products:
        table.insert("", "end", values=product)


def add_item_gui():
    window = tk.Toplevel()
    window.title("Add New Item")
    window.geometry("450x550")

    tk.Label(window, text="ADD NEW ITEM", font=("Arial", 20, "bold")).pack(
        pady=20
    )

    form = tk.Frame(window)
    form.pack(pady=10)

    fields = [
        "Item Name",
        "Category",
        "Buying Price",
        "Selling Price",
        "Quantity",
        "Minimum Stock",
        "Date Added",
    ]
    entries = {}

    for field in fields:
        tk.Label(form, text=field).pack(anchor="w", pady=(8, 2))
        entry = tk.Entry(form, width=40)
        entry.pack()
        entries[field] = entry

    def save_item():
        name = entries["Item Name"].get().strip()
        category = entries["Category"].get().strip()
        buying_price = entries["Buying Price"].get().strip()
        selling_price = entries["Selling Price"].get().strip()
        quantity = entries["Quantity"].get().strip()
        minimum_stock = entries["Minimum Stock"].get().strip()
        date_added = entries["Date Added"].get().strip()

        if not name:
            messagebox.showerror("Error", "Item name cannot be empty.")
            return

        try:
            buying_price = float(buying_price)
            selling_price = float(selling_price)
            quantity = int(quantity)
            minimum_stock = int(minimum_stock)
        except ValueError:
            messagebox.showerror(
                "Error", "Price and quantity fields must contain numbers."
            )
            return

        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO products
            (name, category, buying_price, selling_price, quantity, minimum_stock, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                name,
                category,
                buying_price,
                selling_price,
                quantity,
                minimum_stock,
                date_added,
            ),
        )

        connection.commit()
        connection.close()

        messagebox.showinfo("Success", "Item added successfully!")
        window.destroy()

    tk.Button(window, text="SAVE ITEM", width=20, command=save_item).pack(
        pady=20
    )


def edit_item_gui():
    window = tk.Toplevel()
    window.title("Edit Item")
    window.geometry("450x550")

    tk.Label(window, text="EDIT ITEM", font=("Arial", 20, "bold")).pack(pady=20)

    form = tk.Frame(window)
    form.pack(pady=10)

    tk.Label(form, text="Item ID").pack(anchor="w")
    id_entry = tk.Entry(form, width=40)
    id_entry.pack(pady=5)

    tk.Label(form, text="New Item Name").pack(anchor="w")
    name_entry = tk.Entry(form, width=40)
    name_entry.pack(pady=5)

    tk.Label(form, text="New Category").pack(anchor="w")
    category_entry = tk.Entry(form, width=40)
    category_entry.pack(pady=5)

    tk.Label(form, text="New Buying Price").pack(anchor="w")
    buying_entry = tk.Entry(form, width=40)
    buying_entry.pack(pady=5)

    tk.Label(form, text="New Selling Price").pack(anchor="w")
    selling_entry = tk.Entry(form, width=40)
    selling_entry.pack(pady=5)

    tk.Label(form, text="New Minimum Stock").pack(anchor="w")
    minimum_entry = tk.Entry(form, width=40)
    minimum_entry.pack(pady=5)

    def update_item():
        item_id = id_entry.get().strip()
        name = name_entry.get().strip()
        category = category_entry.get().strip()
        buying_price = buying_entry.get().strip()
        selling_price = selling_entry.get().strip()
        minimum_stock = minimum_entry.get().strip()

        if not item_id:
            messagebox.showerror("Error", "Enter item ID.")
            return

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM products WHERE id = ?", (item_id,))
        item = cursor.fetchone()

        if not item:
            connection.close()
            messagebox.showerror("Error", "Item not found.")
            return

        try:
            buying_price = float(buying_price)
            selling_price = float(selling_price)
            minimum_stock = int(minimum_stock)
        except ValueError:
            connection.close()
            messagebox.showerror("Error", "Enter valid numbers.")
            return

        cursor.execute(
            """
            UPDATE products
            SET name = ?, category = ?, buying_price = ?, selling_price = ?, minimum_stock = ?
            WHERE id = ?
        """,
            (
                name,
                category,
                buying_price,
                selling_price,
                minimum_stock,
                item_id,
            ),
        )

        connection.commit()
        connection.close()

        messagebox.showinfo("Success", "Item updated successfully!")
        window.destroy()

    tk.Button(window, text="UPDATE ITEM", width=20, command=update_item).pack(
        pady=20
    )


def delete_item_gui():
    window = tk.Toplevel()
    window.title("Delete Item")
    window.geometry("400x250")

    tk.Label(window, text="DELETE ITEM", font=("Arial", 20, "bold")).pack(
        pady=20
    )

    tk.Label(window, text="Enter Item ID:").pack()

    id_entry = tk.Entry(window, width=30)
    id_entry.pack(pady=10)

    def delete():
        item_id = id_entry.get().strip()

        if not item_id:
            messagebox.showerror("Error", "Enter an item ID.")
            return

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute("SELECT name FROM products WHERE id = ?", (item_id,))
        item = cursor.fetchone()

        if not item:
            connection.close()
            messagebox.showerror("Error", "Item not found.")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete", f"Are you sure you want to delete '{item[0]}'?"
        )

        if confirm:
            cursor.execute("DELETE FROM products WHERE id = ?", (item_id,))
            connection.commit()
            connection.close()
            messagebox.showinfo("Success", "Item deleted successfully!")
            window.destroy()
        else:
            connection.close()

    tk.Button(window, text="DELETE ITEM", width=20, command=delete).pack(
        pady=15
    )


def add_stock_gui():
    window = tk.Toplevel()
    window.title("Add Stock")
    window.geometry("400x300")

    tk.Label(window, text="ADD STOCK", font=("Arial", 20, "bold")).pack(pady=20)

    tk.Label(window, text="Item ID").pack()
    id_entry = tk.Entry(window, width=30)
    id_entry.pack(pady=5)

    tk.Label(window, text="Quantity to Add").pack()
    amount_entry = tk.Entry(window, width=30)
    amount_entry.pack(pady=5)

    def add():
        try:
            item_id = int(id_entry.get())
            amount = int(amount_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers.")
            return

        if amount <= 0:
            messagebox.showerror("Error", "Quantity must be greater than zero.")
            return

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT name, quantity FROM products WHERE id = ?", (item_id,)
        )
        item = cursor.fetchone()

        if not item:
            connection.close()
            messagebox.showerror("Error", "Item not found.")
            return

        new_quantity = item[1] + amount

        cursor.execute(
            "UPDATE products SET quantity = ? WHERE id = ?",
            (new_quantity, item_id),
        )
        connection.commit()
        connection.close()

        messagebox.showinfo(
            "Success",
            f"{item[0]}\nOld Stock: {item[1]}\nNew Stock: {new_quantity}",
        )
        window.destroy()

    tk.Button(window, text="ADD STOCK", width=20, command=add).pack(pady=20)


def remove_stock_gui():
    window = tk.Toplevel()
    window.title("Remove Stock")
    window.geometry("400x300")

    tk.Label(window, text="REMOVE STOCK", font=("Arial", 20, "bold")).pack(
        pady=20
    )

    tk.Label(window, text="Item ID").pack()
    id_entry = tk.Entry(window, width=30)
    id_entry.pack(pady=5)

    tk.Label(window, text="Quantity to Remove").pack()
    amount_entry = tk.Entry(window, width=30)
    amount_entry.pack(pady=5)

    def remove():
        try:
            item_id = int(id_entry.get())
            amount = int(amount_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers.")
            return

        if amount <= 0:
            messagebox.showerror("Error", "Quantity must be greater than zero.")
            return

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT name, quantity FROM products WHERE id = ?", (item_id,)
        )
        item = cursor.fetchone()

        if not item:
            connection.close()
            messagebox.showerror("Error", "Item not found.")
            return

        if amount > item[1]:
            connection.close()
            messagebox.showerror(
                "Error", "You cannot remove more stock than you have."
            )
            return

        new_quantity = item[1] - amount

        cursor.execute(
            "UPDATE products SET quantity = ? WHERE id = ?",
            (new_quantity, item_id),
        )
        connection.commit()
        connection.close()

        messagebox.showinfo(
            "Success",
            f"{item[0]}\nOld Stock: {item[1]}\nNew Stock: {new_quantity}",
        )
        window.destroy()

    tk.Button(window, text="REMOVE STOCK", width=20, command=remove).pack(
        pady=20
    )


def low_stock_gui():
    window = tk.Toplevel()
    window.title("Low Stock Items")
    window.geometry("700x450")

    tk.Label(window, text="LOW STOCK ITEMS", font=("Arial", 20, "bold")).pack(
        pady=20
    )

    columns = ("ID", "Item", "Quantity", "Minimum Stock")
    table = ttk.Treeview(window, columns=columns, show="headings")

    for column in columns:
        table.heading(column, text=column)
        table.column(column, width=150)

    table.pack(fill="both", expand=True, padx=20, pady=10)

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, quantity, minimum_stock
        FROM products
        WHERE quantity <= minimum_stock
        ORDER BY quantity ASC
    """)

    items = cursor.fetchall()
    connection.close()

    for item in items:
        table.insert("", "end", values=item)

    if not items:
        tk.Label(window, text="No low-stock items.", font=("Arial", 12)).pack(
            pady=10
        )


def sell_item_gui():
    window = tk.Toplevel()
    window.title("Sell Item")
    window.geometry("450x400")

    tk.Label(window, text="SELL ITEM", font=("Arial", 20, "bold")).pack(pady=20)

    form = tk.Frame(window)
    form.pack(pady=10)

    tk.Label(form, text="Item ID").pack(anchor="w")
    id_entry = tk.Entry(form, width=35)
    id_entry.pack(pady=5)

    tk.Label(form, text="Quantity Sold").pack(anchor="w")
    quantity_entry = tk.Entry(form, width=35)
    quantity_entry.pack(pady=5)

    def sell():
        try:
            item_id = int(id_entry.get())
            quantity = int(quantity_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers.")
            return

        if quantity <= 0:
            messagebox.showerror("Error", "Quantity must be greater than zero.")
            return

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name, selling_price, quantity, buying_price
            FROM products
            WHERE id = ?
        """,
            (item_id,),
        )

        item = cursor.fetchone()

        if not item:
            connection.close()
            messagebox.showerror("Error", "Item not found.")
            return

        if quantity > item[2]:
            connection.close()
            messagebox.showerror("Error", "Not enough stock available.")
            return

        total = quantity * item[1]
        new_quantity = item[2] - quantity

        receipt_no = datetime.now().strftime("%Y%m%d%H%M%S")
        sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            UPDATE products
            SET quantity = ?
            WHERE id = ?
        """,
            (new_quantity, item_id),
        )

        cursor.execute(
            """
            INSERT INTO sales
            (product_id, quantity_sold, selling_price, total, sale_date, receipt_no, buying_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                item_id,
                quantity,
                item[1],
                total,
                sale_date,
                receipt_no,
                item[3],
            ),
        )

        connection.commit()
        connection.close()

        messagebox.showinfo(
            "Sale Complete",
            f"Item: {item[0]}\nQuantity: {quantity}\nTotal: ₦{total:,.2f}\nReceipt No: {receipt_no}",
        )
        window.destroy()

    tk.Button(window, text="COMPLETE SALE", width=20, command=sell).pack(
        pady=20
    )


def sales_screen(root, main_area):
    for widget in main_area.winfo_children():
        widget.destroy()

    tk.Label(main_area, text="Sales", font=("Arial", 24, "bold")).pack(pady=30)

    tk.Button(
        main_area, text="Sell Item", width=20, command=sell_item_gui
    ).pack(pady=10)
    tk.Button(
        main_area, text="Multiple Item Sale", width=20, command=multiple_sale_gui
    ).pack(pady=10)
    tk.Button(
        main_area, text="Sales History", width=20, command=sales_history_gui
    ).pack(pady=10)
    tk.Button(
        main_area, text="Search Sales", width=20, command=search_sales_gui
    ).pack(pady=10)


def multiple_sale_gui():
    window = tk.Toplevel()
    window.title("Multiple Item Sale")
    window.geometry("800x600")

    tk.Label(
        window, text="NEW CUSTOMER SALE", font=("Arial", 20, "bold")
    ).pack(pady=15)

    form = tk.Frame(window)
    form.pack(pady=10)

    tk.Label(form, text="Item ID").grid(row=0, column=0, padx=5)
    id_entry = tk.Entry(form, width=15)
    id_entry.grid(row=0, column=1, padx=5)

    tk.Label(form, text="Quantity").grid(row=0, column=2, padx=5)
    quantity_entry = tk.Entry(form, width=15)
    quantity_entry.grid(row=0, column=3, padx=5)

    columns = ("Item", "Quantity", "Price", "Total")
    table = ttk.Treeview(window, columns=columns, show="headings")

    for column in columns:
        table.heading(column, text=column)
        table.column(column, width=150)

    table.pack(fill="both", expand=True, padx=20, pady=20)

    items_bought = []
    grand_total = 0

    total_label = tk.Label(
        window, text="Grand Total: ₦0.00", font=("Arial", 16, "bold")
    )
    total_label.pack(pady=10)

    def add_to_cart():
        nonlocal grand_total

        try:
            item_id = int(id_entry.get())
            quantity = int(quantity_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers.")
            return

        if quantity <= 0:
            messagebox.showerror("Error", "Quantity must be greater than zero.")
            return

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name, selling_price, quantity, buying_price
            FROM products
            WHERE id = ?
        """,
            (item_id,),
        )

        item = cursor.fetchone()
        connection.close()

        if not item:
            messagebox.showerror("Error", "Item not found.")
            return

        if quantity > item[2]:
            messagebox.showerror("Error", "Not enough stock available.")
            return

        total = quantity * item[1]
        items_bought.append(
            (item_id, item[0], quantity, item[1], item[3], total)
        )

        grand_total += total

        table.insert(
            "",
            "end",
            values=(item[0], quantity, f"₦{item[1]:,.2f}", f"₦{total:,.2f}"),
        )
        total_label.config(text=f"Grand Total: ₦{grand_total:,.2f}")

        id_entry.delete(0, tk.END)
        quantity_entry.delete(0, tk.END)

    def complete_sale():
        nonlocal grand_total
        if not items_bought:
            messagebox.showerror("Error", "No items have been added.")
            return

        receipt_no = datetime.now().strftime("%Y%m%d%H%M%S")
        sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection = connect_db()
        cursor = connection.cursor()

        for item in items_bought:
            item_id = item[0]
            quantity = item[2]
            selling_price = item[3]
            buying_price = item[4]
            total = item[5]

            cursor.execute(
                "SELECT quantity FROM products WHERE id = ?", (item_id,)
            )
            current_stock = cursor.fetchone()

            if not current_stock or quantity > current_stock[0]:
                connection.close()
                messagebox.showerror(
                    "Error", f"Not enough stock for {item[1]}."
                )
                return

            new_quantity = current_stock[0] - quantity

            cursor.execute(
                """
                UPDATE products
                SET quantity = ?
                WHERE id = ?
            """,
                (new_quantity, item_id),
            )

            cursor.execute(
                """
                INSERT INTO sales
                (product_id, quantity_sold, selling_price, total, sale_date, receipt_no, buying_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    item_id,
                    quantity,
                    selling_price,
                    total,
                    sale_date,
                    receipt_no,
                    buying_price,
                ),
            )

        connection.commit()
        connection.close()

        receipt_text = f"Receipt No: {receipt_no}\n\n"
        for item in items_bought:
            receipt_text += f"{item[1]}  x{item[2]}  = ₦{item[5]:,.2f}\n"

        receipt_text += (
            f"\nGRAND TOTAL: ₦{grand_total:,.2f}\nDate: {sale_date}\n\nThank you!"
        )

        messagebox.showinfo("Sale Complete", receipt_text)
        window.destroy()

    tk.Button(form, text="ADD TO RECEIPT", command=add_to_cart).grid(
        row=0, column=4, padx=10
    )
    tk.Button(
        window, text="COMPLETE SALE", width=20, command=complete_sale
    ).pack(pady=15)


def sales_history_gui():
    window = tk.Toplevel()
    window.title("Sales History")
    window.geometry("950x500")

    tk.Label(window, text="SALES HISTORY", font=("Arial", 20, "bold")).pack(
        pady=15
    )

    columns = (
        "Sale ID",
        "Item",
        "Quantity",
        "Selling Price",
        "Total",
        "Date",
        "Receipt No",
    )
    table = ttk.Treeview(window, columns=columns, show="headings")

    for column in columns:
        table.heading(column, text=column)
        table.column(column, width=120)

    table.pack(fill="both", expand=True, padx=15, pady=15)

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT sales.sale_id,
               products.name,
               sales.quantity_sold,
               sales.selling_price,
               sales.total,
               sales.sale_date,
               sales.receipt_no
        FROM sales
        JOIN products ON sales.product_id = products.id
        ORDER BY sales.sale_id DESC
    """)

    sales = cursor.fetchall()
    connection.close()

    for sale in sales:
        table.insert(
            "",
            "end",
            values=(
                sale[0],
                sale[1],
                sale[2],
                f"₦{sale[3]:,.2f}",
                f"₦{sale[4]:,.2f}",
                sale[5],
                sale[6],
            ),
        )


def search_sales_gui():
    window = tk.Toplevel()
    window.title("Search Sales")
    window.geometry("950x550")

    tk.Label(window, text="SEARCH SALES", font=("Arial", 20, "bold")).pack(
        pady=15
    )

    search_frame = tk.Frame(window)
    search_frame.pack(pady=10)

    tk.Label(search_frame, text="Item Name:").pack(side="left", padx=5)
    search_entry = tk.Entry(search_frame, width=30)
    search_entry.pack(side="left", padx=5)

    columns = (
        "Sale ID",
        "Item",
        "Quantity",
        "Selling Price",
        "Total",
        "Date",
        "Receipt No",
    )
    table = ttk.Treeview(window, columns=columns, show="headings")

    for column in columns:
        table.heading(column, text=column)
        table.column(column, width=120)

    table.pack(fill="both", expand=True, padx=15, pady=15)

    def search():
        for row in table.get_children():
            table.delete(row)

        search_text = search_entry.get().strip()

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT sales.sale_id,
                   products.name,
                   sales.quantity_sold,
                   sales.selling_price,
                   sales.total,
                   sales.sale_date,
                   sales.receipt_no
            FROM sales
            JOIN products ON sales.product_id = products.id
            WHERE products.name LIKE ?
            ORDER BY sales.sale_id DESC
        """,
            (f"%{search_text}%",),
        )

        sales = cursor.fetchall()
        connection.close()

        for sale in sales:
            table.insert(
                "",
                "end",
                values=(
                    sale[0],
                    sale[1],
                    sale[2],
                    f"₦{sale[3]:,.2f}",
                    f"₦{sale[4]:,.2f}",
                    sale[5],
                    sale[6],
                ),
            )

        if not sales:
            messagebox.showinfo("Search", "No sales found.")

    tk.Button(search_frame, text="SEARCH", command=search).pack(
        side="left", padx=5
    )


def add_expense_gui():
    window = tk.Toplevel()
    window.title("Add Expense")
    window.geometry("450x400")

    tk.Label(window, text="ADD EXPENSE", font=("Arial", 20, "bold")).pack(
        pady=20
    )

    form = tk.Frame(window)
    form.pack(pady=10)

    tk.Label(form, text="Description").pack(anchor="w")
    description_entry = tk.Entry(form, width=40)
    description_entry.pack(pady=5)

    tk.Label(form, text="Amount").pack(anchor="w")
    amount_entry = tk.Entry(form, width=40)
    amount_entry.pack(pady=5)

    tk.Label(form, text="Category").pack(anchor="w")
    category_entry = tk.Entry(form, width=40)
    category_entry.pack(pady=5)

    tk.Label(form, text="Date (YYYY-MM-DD)").pack(anchor="w")
    date_entry = tk.Entry(form, width=40)
    date_entry.pack(pady=5)

    def save_expense():
        description = description_entry.get().strip()
        amount = amount_entry.get().strip()
        category = category_entry.get().strip()
        expense_date = date_entry.get().strip()

        if not description:
            messagebox.showerror("Error", "Enter an expense description.")
            return

        if not category:
            messagebox.showerror("Error", "Enter an expense category.")
            return

        try:
            amount = float(amount)
        except ValueError:
            messagebox.showerror("Error", "Amount must be a number.")
            return

        if amount <= 0:
            messagebox.showerror("Error", "Amount must be greater than zero.")
            return

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO expenses
            (description, amount, category, expense_date)
            VALUES (?, ?, ?, ?)
        """,
            (description, amount, category, expense_date),
        )

        connection.commit()
        connection.close()

        messagebox.showinfo("Success", "Expense added successfully!")
        window.destroy()

    tk.Button(window, text="SAVE EXPENSE", width=20, command=save_expense).pack(
        pady=20
    )


def expenses_history_gui():
    window = tk.Toplevel()
    window.title("Expense History")
    window.geometry("800x500")

    tk.Label(window, text="EXPENSE HISTORY", font=("Arial", 20, "bold")).pack(
        pady=15
    )

    columns = ("ID", "Description", "Amount", "Category", "Date")
    table = ttk.Treeview(window, columns=columns, show="headings")

    for column in columns:
        table.heading(column, text=column)
        table.column(column, width=140)

    table.pack(fill="both", expand=True, padx=15, pady=15)

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT expense_id, description, amount, category, expense_date
        FROM expenses
        ORDER BY expense_id DESC
    """)

    expenses = cursor.fetchall()
    connection.close()

    for expense in expenses:
        table.insert(
            "",
            "end",
            values=(
                expense[0],
                expense[1],
                f"₦{expense[2]:,.2f}",
                expense[3],
                expense[4],
            ),
        )


def expenses_screen(root, main_area):
    for widget in main_area.winfo_children():
        widget.destroy()

    tk.Label(main_area, text="Expenses", font=("Arial", 24, "bold")).pack(
        pady=30
    )

    tk.Button(
        main_area, text="Add Expense", width=20, command=add_expense_gui
    ).pack(pady=10)
    tk.Button(
        main_area, text="Expense History", width=20, command=expenses_history_gui
    ).pack(pady=10)


def financial_summary_gui():
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM sales")
    total_sales = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
    total_expenses = cursor.fetchone()[0]

    connection.close()

    profit = total_sales - total_expenses

    messagebox.showinfo(
        "Financial Summary",
        f"Total Sales: ₦{total_sales:,.2f}\n"
        f"Total Expenses: ₦{total_expenses:,.2f}\n"
        f"Profit/Loss: ₦{profit:,.2f}",
    )


def product_profit_gui():
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT products.name,
               SUM((sales.selling_price - sales.buying_price) * sales.quantity_sold)
        FROM sales
        JOIN products ON sales.product_id = products.id
        GROUP BY products.id
        ORDER BY 2 DESC
    """)

    profits = cursor.fetchall()
    connection.close()

    if not profits:
        messagebox.showinfo("Product Profit", "No sales available.")
        return

    text = "PRODUCT PROFIT\n\n"
    for item in profits:
        text += f"{item[0]}: ₦{item[1]:,.2f}\n"

    messagebox.showinfo("Product Profit", text)


def reports_screen(root, main_area):
    for widget in main_area.winfo_children():
        widget.destroy()

    tk.Label(main_area, text="Reports", font=("Arial", 24, "bold")).pack(pady=30)

    tk.Button(
        main_area,
        text="Financial Summary",
        width=25,
        command=financial_summary_gui,
    ).pack(pady=8)
    tk.Button(
        main_area, text="Product Profit", width=25, command=product_profit_gui
    ).pack(pady=8)
    tk.Button(
        main_area, text="Daily Report", width=25, command=daily_report_gui
    ).pack(pady=8)
    tk.Button(
        main_area, text="Weekly Report", width=25, command=weekly_report_gui
    ).pack(pady=8)
    tk.Button(
        main_area, text="Monthly Report", width=25, command=monthly_report_gui
    ).pack(pady=8)


def daily_report_gui():
    window = tk.Toplevel()
    window.title("Daily Report")
    window.geometry("400x300")

    tk.Label(window, text="DAILY REPORT", font=("Arial", 20, "bold")).pack(
        pady=20
    )
    tk.Label(window, text="Enter Date (YYYY-MM-DD)").pack()

    date_entry = tk.Entry(window, width=30)
    date_entry.pack(pady=10)

    def generate():
        date = date_entry.get().strip()

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COALESCE(SUM(total), 0)
            FROM sales
            WHERE DATE(sale_date) = ?
        """,
            (date,),
        )
        sales = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE expense_date = ?
        """,
            (date,),
        )
        expenses = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COALESCE(SUM((selling_price - buying_price) * quantity_sold), 0)
            FROM sales
            WHERE DATE(sale_date) = ?
        """,
            (date,),
        )
        profit = cursor.fetchone()[0]

        connection.close()

        net = profit - expenses

        messagebox.showinfo(
            "Daily Report",
            f"Date: {date}\n\n"
            f"Sales: ₦{sales:,.2f}\n"
            f"Expenses: ₦{expenses:,.2f}\n"
            f"Product Profit: ₦{profit:,.2f}\n"
            f"Net Profit: ₦{net:,.2f}",
        )

    tk.Button(window, text="GENERATE REPORT", width=20, command=generate).pack(
        pady=20
    )


def weekly_report_gui():
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM sales
        WHERE DATE(sale_date) >= DATE('now', '-6 days')
    """)
    sales = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE DATE(expense_date) >= DATE('now', '-6 days')
    """)
    expenses = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM((selling_price - buying_price) * quantity_sold), 0)
        FROM sales
        WHERE DATE(sale_date) >= DATE('now', '-6 days')
    """)
    profit = cursor.fetchone()[0]

    connection.close()

    net = profit - expenses

    messagebox.showinfo(
        "Weekly Report",
        "LAST 7 DAYS\n\n"
        f"Sales: ₦{sales:,.2f}\n"
        f"Expenses: ₦{expenses:,.2f}\n"
        f"Product Profit: ₦{profit:,.2f}\n"
        f"Net Profit: ₦{net:,.2f}",
    )


def monthly_report_gui():
    window = tk.Toplevel()
    window.title("Monthly Report")
    window.geometry("400x300")

    tk.Label(window, text="MONTHLY REPORT", font=("Arial", 20, "bold")).pack(
        pady=20
    )
    tk.Label(window, text="Enter Month (YYYY-MM)").pack()

    month_entry = tk.Entry(window, width=30)
    month_entry.pack(pady=10)

    def generate():
        month = month_entry.get().strip()

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COALESCE(SUM(total), 0)
            FROM sales
            WHERE strftime('%Y-%m', sale_date) = ?
        """,
            (month,),
        )
        sales = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE strftime('%Y-%m', expense_date) = ?
        """,
            (month,),
        )
        expenses = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COALESCE(SUM((selling_price - buying_price) * quantity_sold), 0)
            FROM sales
            WHERE strftime('%Y-%m', sale_date) = ?
        """,
            (month,),
        )
        profit = cursor.fetchone()[0]

        connection.close()

        net = profit - expenses

        messagebox.showinfo(
            "Monthly Report",
            f"Month: {month}\n\n"
            f"Sales: ₦{sales:,.2f}\n"
            f"Expenses: ₦{expenses:,.2f}\n"
            f"Product Profit: ₦{profit:,.2f}\n"
            f"Net Profit: ₦{net:,.2f}",
        )

    tk.Button(window, text="GENERATE REPORT", width=20, command=generate).pack(
        pady=20
    )


def dashboard_screen(root, main_area):
    for widget in main_area.winfo_children():
        widget.destroy()

    tk.Label(main_area, text="Dashboard", font=("Arial", 26, "bold")).pack(
        pady=20
    )

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(quantity), 0) FROM products")
    total_quantity = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COALESCE(SUM(buying_price * quantity), 0) FROM products"
    )
    stock_value = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM sales")
    total_sales = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
    total_expenses = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM((selling_price - buying_price) * quantity_sold), 0)
        FROM sales
    """)
    product_profit = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM products WHERE quantity <= minimum_stock"
    )
    low_stock_count = cursor.fetchone()[0]

    connection.close()

    net_profit = product_profit - total_expenses

    cards = tk.Frame(main_area)
    cards.pack(pady=20)

    def create_card(parent, title, value, row, column):
        card = tk.Frame(
            parent, relief="ridge", borderwidth=2, width=220, height=120
        )
        card.grid(row=row, column=column, padx=10, pady=10)
        card.grid_propagate(False)

        tk.Label(card, text=title, font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(card, text=value, font=("Arial", 18, "bold")).pack()

    create_card(cards, "Total Products", str(total_products), 0, 0)
    create_card(cards, "Total Quantity", str(total_quantity), 0, 1)
    create_card(cards, "Stock Value", f"₦{stock_value:,.2f}", 0, 2)
    create_card(cards, "Total Sales", f"₦{total_sales:,.2f}", 1, 0)
    create_card(cards, "Total Expenses", f"₦{total_expenses:,.2f}", 1, 1)
    create_card(cards, "Profit / Loss", f"₦{net_profit:,.2f}", 1, 2)
    create_card(cards, "Low Stock", str(low_stock_count), 2, 0)


def export_screen(root, main_area):
    for widget in main_area.winfo_children():
        widget.destroy()

    tk.Label(main_area, text="Export Data", font=("Arial", 24, "bold")).pack(
        pady=30
    )

    tk.Button(
        main_area, text="Export Products", width=25, command=export_products
    ).pack(pady=10)
    tk.Button(
        main_area, text="Export Sales", width=25, command=export_sales
    ).pack(pady=10)
    tk.Button(
        main_area, text="Export Expenses", width=25, command=export_expenses
    ).pack(pady=10)


def backup_screen(root, main_area):
    for widget in main_area.winfo_children():
        widget.destroy()

    tk.Label(
        main_area, text="Database Backup", font=("Arial", 24, "bold")
    ).pack(pady=30)
    tk.Label(
        main_area,
        text="Create a copy of your shop database.",
        font=("Arial", 12),
    ).pack(pady=10)

    tk.Button(
        main_area, text="CREATE BACKUP", width=25, command=backup_database
    ).pack(pady=20)


def start_gui():
    create_tables()

    root = tk.Tk()
    root.title("My Shop Manager")
    root.geometry("1100x650")
    root.minsize(900, 550)

    main_area = tk.Frame(root)
    main_area.pack(side="right", fill="both", expand=True)

    sidebar = tk.Frame(root, width=220)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    tk.Label(sidebar, text="MY SHOP", font=("Arial", 20, "bold")).pack(pady=30)

    tk.Button(
        sidebar,
        text="Dashboard",
        width=20,
        command=lambda: dashboard_screen(root, main_area),
    ).pack(pady=5)
    tk.Button(
        sidebar,
        text="Inventory",
        width=20,
        command=lambda: inventory_screen(root, main_area),
    ).pack(pady=5)
    tk.Button(
        sidebar,
        text="Sales",
        width=20,
        command=lambda: sales_screen(root, main_area),
    ).pack(pady=5)
    tk.Button(
        sidebar,
        text="Expenses",
        width=20,
        command=lambda: expenses_screen(root, main_area),
    ).pack(pady=5)
    tk.Button(
        sidebar,
        text="Reports",
        width=20,
        command=lambda: reports_screen(root, main_area),
    ).pack(pady=5)
    tk.Button(
        sidebar,
        text="Export",
        width=20,
        command=lambda: export_screen(root, main_area),
    ).pack(pady=5)
    tk.Button(
        sidebar,
        text="Backup",
        width=20,
        command=lambda: backup_screen(root, main_area),
    ).pack(pady=5)
    tk.Button(sidebar, text="Exit", width=20, command=root.destroy).pack(
        pady=30
    )

    dashboard_screen(root, main_area)
    root.mainloop()


if __name__ == "__main__":
    start_gui()
