import qrcode

data = "faith adigun"

qr = qrcode.make(data)

qr.save("qrcode.png")

print("QR generate")