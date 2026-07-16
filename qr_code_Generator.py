import qrcode
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox

# Global variable for logo path
logo_path = None

# Function to select logo
def select_logo():
    global logo_path
    logo_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
    )
    if logo_path:
        logo_label.config(text="Logo Selected ✅")

# Function to generate QR
def generate_qr():
    data = entry.get()

    if not data:
        messagebox.showerror("Error", "Please enter a link or text")
        return

    # Create QR
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Add logo if selected
    if logo_path:
        logo = Image.open(logo_path)
        logo = logo.resize((80, 80))

        x = (img.size[0] - logo.size[0]) // 2
        y = (img.size[1] - logo.size[1]) // 2

        img.paste(logo, (x, y))

    # Save QR
    img.save("generated_qr.png")

    # Display QR in app
    img_display = ImageTk.PhotoImage(img.resize((200, 200)))
    qr_label.config(image=img_display)
    qr_label.image = img_display

    messagebox.showinfo("Success", "QR Code Generated!")

# Create window
root = tk.Tk()
root.title("QR Code Generator App")
root.geometry("350x450")

# Title
title = tk.Label(root, text="QR Code Generator", font=("Arial", 16, "bold"))
title.pack(pady=10)

# Input field
entry = tk.Entry(root, width=30)
entry.pack(pady=10)
entry.insert(0, "Enter link or text")

# Logo button
logo_btn = tk.Button(root, text="Upload Logo", command=select_logo)
logo_btn.pack(pady=5)

logo_label = tk.Label(root, text="No Logo Selected")
logo_label.pack()

# Generate button
gen_btn = tk.Button(root, text="Generate QR", command=generate_qr, bg="green", fg="white")
gen_btn.pack(pady=10)

# QR display
qr_label = tk.Label(root)
qr_label.pack(pady=10)

# Run app
root.mainloop()