import random
import smtplib
import socket

class OTP:
    def __init__(self):
        print("=" * 3, "Welcome to OTP verification point", "=" * 3)

    @staticmethod
    def welcome():
        Email = input("Enter your Email: ")
        print(f"✅ Email captured: {Email}")
        return Email

    @staticmethod
    def Otp(receiver_email):
        print("🔐 Generating OTP...")
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        otp = "".join(random.choice(letters) for _ in range(5))
        print(f"✅ OTP generated: {otp}")

        sender_email = "danadigun96@gmail.com"
        app_password = "jvdshblkpocwenyv"  # REPLACE THIS!

        message = f"Subject: OTP Verification\n\nYour OTP is: {otp}"

        print("📧 Attempting to send email...")
        
        # Try different methods
        methods = [
            ("587", smtplib.SMTP, True),  # TLS
            ("465", smtplib.SMTP_SSL, False)  # SSL
        ]
        
        for port, smtp_class, use_tls in methods:
            try:
                print(f"   Trying port {port}...")
                if use_tls:
                    server = smtp_class("smtp.gmail.com", int(port))
                    server.starttls()
                else:
                    server = smtp_class("smtp.gmail.com", int(port))
                
                server.login(sender_email, app_password)
                server.sendmail(sender_email, receiver_email, message)
                server.quit()
                print(f"✅ OTP sent successfully via port {port}!")
                return
                
            except Exception as e:
                print(f"   ❌ Port {port} failed: {e}")
                continue
        
        print("\n❌ All connection methods failed!")
        print("Please check:")
        print("  1. Internet connection")
        print("  2. Firewall settings")
        print("  3. If using VPN, try disconnecting")
        print("  4. Try on a different network (mobile hotspot)")

# Run
if __name__ == "__main__":
    email = OTP.welcome()
    OTP.Otp(email)