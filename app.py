from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from datetime import datetime
import re
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "my_journal_secret_key"

# ==============================================================================
# SQLITE DATABASE (Works on Pylori 3 without any extra setup)
# ==============================================================================

DB_PATH = 'journal.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they don't exist"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT
        )
    ''')
    
    # Profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            username TEXT PRIMARY KEY,
            display_name TEXT,
            bio TEXT,
            avatar TEXT,
            dob TEXT,
            timezone TEXT,
            email_verified INTEGER,
            updated_at TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')
    
    # Entries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            title TEXT,
            date TEXT,
            time TEXT,
            mood TEXT,
            mood_emoji TEXT,
            tag TEXT,
            image TEXT,
            content TEXT,
            is_private INTEGER,
            created_at TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            username TEXT PRIMARY KEY,
            notifications TEXT,
            privacy TEXT,
            theme TEXT,
            backup TEXT,
            account TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Seed data if empty
    seed_database()

def seed_database():
    """Add sample data if database is empty"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("📦 Seeding database with sample data...")
        
        # Sample users with hashed passwords
        users = [
            ("Alex", generate_password_hash("Password@123"), "alex@example.com", datetime.now().isoformat()),
            ("Ade", generate_password_hash("Password@123"), "ade@example.com", datetime.now().isoformat()),
            ("Yemi", generate_password_hash("Password@123"), "yemi@example.com", datetime.now().isoformat())
        ]
        cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", users)
        
        # Sample profiles
        profiles = [
            ("Alex", "Olivia", "The pages you write today create the life you live tomorrow.", 
             "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop&q=80",
             "1998-05-14", "UTC-5 (EST)", 1, datetime.now().isoformat()),
            ("Ade", "Ade", "Ade's personal thoughts.",
             "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&auto=format&fit=crop&q=80",
             "2000-01-01", "UTC+1 (WAT)", 1, datetime.now().isoformat()),
            ("Yemi", "Yemi", "Yemi's personal journal.",
             "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=100&auto=format&fit=crop&q=80",
             "1999-10-20", "UTC+1 (WAT)", 0, datetime.now().isoformat())
        ]
        cursor.executemany("INSERT INTO profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?)", profiles)
        
        # Sample entry for Alex
        entries = [
            ("Alex", "A Perfect Sunset", "Aug 13, 2026", "06:45 PM", "Happy", "😊", "Entities",
             "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=200&auto=format&fit=crop&q=60",
             "The sky was painted with shades of orange and pink tonight. Moments like these remind me to <b>slow down</b>...",
             0, datetime.now().isoformat())
        ]
        cursor.executemany("INSERT INTO entries (username, title, date, time, mood, mood_emoji, tag, image, content, is_private, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", entries)
        
        # Default settings
        import json
        default_notifications = json.dumps({
            "daily_reminder": True, "reminder_time": "20:00", "reminder_freq": "Daily",
            "push_enabled": True, "email_summaries": False, "streak_alerts": True,
            "security_alerts": True, "quiet_hours": True, "quiet_start": "22:00", "quiet_end": "07:00"
        })
        default_privacy = json.dumps({
            "passcode_enabled": False, "biometric_enabled": True, "auto_lock": "1min",
            "default_private": True, "hide_previews": False, "blur_app": True,
            "e2ee": True, "cloud_provider": "App Server", "analytics": False
        })
        default_theme = json.dumps({
            "mode": "Light", "preset": "Pastel Lavender", "accent_color": "#8e7cc3",
            "font_style": "Georgia", "font_size": "Medium", "texture": "Plain White", "layout": "Standard"
        })
        default_backup = json.dumps({
            "auto_sync": True, "sync_freq": "Real-time", "network": "Wi-Fi Only",
            "destination": "App Cloud", "last_backup": "Aug 13, 2026 09:41 AM"
        })
        default_account = json.dumps({
            "2fa_enabled": False, "plan": "Journal Pro", "storage_used": "1.2 GB of 5.0 GB"
        })
        
        for username in ["Alex", "Ade", "Yemi"]:
            cursor.execute(
                "INSERT INTO settings (username, notifications, privacy, theme, backup, account) VALUES (?, ?, ?, ?, ?, ?)",
                (username, default_notifications, default_privacy, default_theme, default_backup, default_account)
            )
        
        conn.commit()
        print("✅ Sample data seeded successfully!")
    
    conn.close()

# Initialize database
init_db()

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_user_settings(username):
    """Get settings for a user"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        import json
        return {
            "notifications": json.loads(result["notifications"]),
            "privacy": json.loads(result["privacy"]),
            "theme": json.loads(result["theme"]),
            "backup": json.loads(result["backup"]),
            "account": json.loads(result["account"])
        }
    return None

def update_setting(username, category, data):
    """Update a specific setting category"""
    import json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE settings SET {category} = ? WHERE username = ?",
        (json.dumps(data), username)
    )
    conn.commit()
    conn.close()

def is_valid_username(username):
    if len(username) < 3 or len(username) > 15:
        return False, "Username must be between 3 and 15 characters long."
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores (_)."
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
    exists = cursor.fetchone()[0] > 0
    conn.close()
    
    if exists:
        return False, "Username already taken."
    return True, "Valid username!"

def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&*)."
    return True, "Strong password!"

# ==============================================================================
# CSS STYLESHEET (UPDATED WITH PASSWORD TOGGLE STYLES)
# ==============================================================================

BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
.auth-bg { background: linear-gradient(135deg, #fbe7d5 0%, #e2d7f8 50%, #cbe3f7 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 15px; }
.auth-card { background: rgba(255, 255, 255, 0.95); width: 100%; max-width: 360px; padding: 40px 30px; border-radius: 24px; text-align: center; box-shadow: 0 15px 35px rgba(108, 92, 231, 0.08); backdrop-filter: blur(10px); }
.auth-logo-icon { width: 60px; height: 60px; background: #f2eafd; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px auto; font-size: 28px; }
.auth-title { font-family: Georgia, serif; font-size: 24px; color: #2d3436; font-weight: bold; margin-bottom: 4px; }
.auth-subtitle { font-size: 11px; color: #a0aec0; margin-bottom: 25px; }
.input-group { position: relative; margin-bottom: 12px; }
.input-group .icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); font-size: 13px; color: #a0aec0; z-index: 1; }
.input-group input { width: 100%; padding: 11px 38px; border: 1px solid #edf2f7; border-radius: 12px; font-size: 12px; outline: none; background: #f8fafc; color: #2d3436; transition: border-color 0.3s; }
.input-group input:focus { border-color: #8a6cf0; background: #ffffff; }

/* Password toggle button */
.password-toggle {
    position: absolute;
    right: 14px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    cursor: pointer;
    font-size: 16px;
    color: #a0aec0;
    padding: 5px;
    z-index: 1;
    transition: color 0.3s;
}
.password-toggle:hover { color: #6155f5; }
.password-toggle:focus { outline: none; }

.input-group .icon { left: 14px; }
.input-group input { padding: 11px 44px 11px 38px; }

.btn-auth-primary { background: linear-gradient(135deg, #8a6cf0 0%, #6155f5 100%); color: white; border: none; padding: 12px; border-radius: 12px; font-size: 12px; font-weight: bold; width: 100%; cursor: pointer; text-transform: uppercase; transition: transform 0.2s; }
.btn-auth-primary:hover { transform: scale(1.02); }
.btn-auth-primary:active { transform: scale(0.98); }

body.dashboard-body { background: #f4f3f8; min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 15px; }
.app-window { background: #ffffff; width: 100%; max-width: 1180px; min-height: 760px; border-radius: 24px; box-shadow: 0 20px 40px rgba(0,0,0,0.04); overflow: hidden; display: flex; flex-direction: column; }
@media (min-width: 900px) { .app-window { flex-direction: row; } }

.sidebar { width: 100%; background: #fcfbfe; padding: 24px 18px; border-bottom: 1px solid #f0edf5; display: flex; flex-direction: column; justify-content: space-between; }
@media (min-width: 900px) { .sidebar { width: 210px; border-bottom: none; border-right: 1px solid #f0edf5; } }
.brand h2 { font-family: Georgia, serif; color: #7c68a4; font-size: 20px; font-weight: 500; font-style: italic; }
.brand p { font-size: 10px; color: #a0a0b0; margin-top: 2px; }
.nav-links { list-style: none; display: flex; flex-wrap: wrap; gap: 4px; margin-top: 20px; }
@media (min-width: 900px) { .nav-links { flex-direction: column; } }
.nav-links a { text-decoration: none; color: #636e72; padding: 9px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; display: flex; align-items: center; gap: 10px; }
.nav-links a.active { background: #8e7cc3; color: white; font-weight: 600; }
.main-content { flex: 1; padding: 25px 35px; overflow-y: auto; background: #ffffff; }

.settings-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
.settings-header h1 { font-family: Georgia, serif; font-size: 22px; color: #2d2a32; font-weight: 600; }
.settings-list { display: flex; flex-direction: column; gap: 14px; max-width: 800px; }
.settings-item { display: flex; align-items: center; justify-content: space-between; background: #faf9fc; border: 1px solid #f2f0f7; border-radius: 16px; padding: 14px 18px; text-decoration: none; color: inherit; }
.settings-item:hover { border-color: #e2dcf0; background: #f7f5fb; }
.settings-left { display: flex; align-items: center; gap: 14px; }
.icon-box { width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.icon-purple { background: #eae6f7; color: #7c68a4; }
.icon-yellow { background: #fef5e6; color: #e6a13c; }
.icon-green { background: #e8f7f2; color: #34b38a; }
.icon-blue { background: #e8f3fb; color: #409eff; }
.icon-amber { background: #fdf3e7; color: #d9822b; }
.icon-pink { background: #fcebf0; color: #e05277; }
.settings-info h3 { font-size: 13px; font-weight: 600; color: #2d2a32; margin-bottom: 2px; }
.settings-info p { font-size: 11px; color: #928e9c; }

.profile-card { background: #ffffff; border: 1px solid #f0edf5; border-radius: 20px; padding: 25px; max-width: 800px; }
.profile-section-title { font-size: 13px; font-weight: 700; color: #7c68a4; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 14px; margin-top: 20px; display: flex; align-items: center; gap: 8px; }
.profile-section-title:first-of-type { margin-top: 0; }
.form-grid-2 { display: grid; grid-template-columns: 1fr; gap: 16px; margin-bottom: 12px; }
@media (min-width: 600px) { .form-grid-2 { grid-template-columns: 1fr 1fr; } }
.field-box { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.field-label { font-size: 11px; font-weight: 600; color: #5a5568; }
.field-input { width: 100%; padding: 10px 14px; border: 1px solid #e2dcf0; border-radius: 10px; font-size: 12px; outline: none; background: #faf9fc; color: #2d2a32; }

.profile-form-footer { display: flex; justify-content: flex-end; gap: 12px; margin-top: 30px; padding-top: 18px; border-top: 1px solid #f2f0f7; }

.btn-primary { background: #8e7cc3; color: white; border: none; padding: 8px 16px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; text-decoration: none; }
.btn-secondary { background: #f1f2f6; color: #2d3436; border: 1px solid #e2e8f0; padding: 7px 14px; border-radius: 8px; font-size: 11px; text-decoration: none; cursor: pointer; font-weight: 600; }
.switch { position: relative; display: inline-block; width: 38px; height: 22px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #e2dcf0; transition: .3s; border-radius: 22px; }
.slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px; background-color: white; transition: .3s; border-radius: 50%; }
input:checked + .slider { background-color: #7c68a4; }
input:checked + .slider:before { transform: translateX(16px); }

.toggle-row { display: flex; justify-content: space-between; align-items: center; background: #faf9fc; border: 1px solid #f2f0f7; padding: 12px 16px; border-radius: 12px; margin-bottom: 10px; }
.toggle-title { font-size: 12px; font-weight: 600; color: #2d2a32; }
.toggle-desc { font-size: 10px; color: #928e9c; margin-top: 2px; }
.success-msg { color: #2e7d32; font-size: 11px; background: #e8f5e9; padding: 8px 12px; border-radius: 8px; margin-bottom: 15px; }
.error-msg { color: #d32f2f; font-size: 11px; background: #ffebee; padding: 8px 12px; border-radius: 8px; margin-bottom: 15px; }
.flash-messages { margin-bottom: 15px; }
"""

# ==============================================================================
# LAYOUT TEMPLATE
# ==============================================================================

def layout(content, active_page="settings"):
    """Main layout template"""
    current_user = session.get("user", "User")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT bio FROM profiles WHERE username = ?", (current_user,))
    profile = cursor.fetchone()
    conn.close()
    
    if profile:
        bio = profile["bio"]
    else:
        bio = "The pages you write today create the life you live tomorrow."
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>My Journal</title>
        <style>{BASE_CSS}</style>
    </head>
    <body class="dashboard-body">
        <div class="app-window">
            <aside class="sidebar">
                <div>
                    <div class="brand">
                        <h2>My Journal ♡</h2>
                        <p>Capture. Reflect. Grow.</p>
                    </div>
                    <ul class="nav-links">
                        <li><a href="/dashboard">🏠 Home</a></li>
                        <li><a href="/dashboard">📖 Entries</a></li>
                        <li><a href="/settings" class="{'active' if active_page == 'settings' else ''}">⚙️ Settings</a></li>
                    </ul>
                </div>
                <div>
                    <div style="background: #f3f0f9; border-radius: 16px; padding: 15px; text-align: center; margin-top: 20px;">
                        <p style="font-size: 11px; color: #5a5568; font-style: italic;">{bio}</p>
                    </div>
                    <div style="margin-top: 12px; text-align: center;">
                        <a href="/logout" style="text-decoration: none; color: #b2bec3; font-size: 11px; font-weight: 600;">🚪 Logout</a>
                    </div>
                </div>
            </aside>
            <main class="main-content">{content}</main>
        </div>
    </body>
    </html>
    """

# ==============================================================================
# AUTH ROUTES (UPDATED WITH PASSWORD TOGGLE)
# ==============================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page with password show/hide toggle"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user["password"], password):
            session["user"] = username
            flash(f"Welcome back, {username}! ✨", "success")
            return redirect(url_for("settings"))
        else:
            flash("Invalid username or password.", "error")
    
    # Get flash messages
    flash_messages = ""
    for category, message in get_flashed_messages():
        css_class = "success-msg" if category == "success" else "error-msg"
        flash_messages += f'<p class="{css_class}">{message}</p>'
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - My Journal</title>
        <style>{BASE_CSS}</style>
        <script>
            // JavaScript for password toggle
            function togglePassword() {{
                const passwordInput = document.getElementById('password');
                const toggleBtn = document.getElementById('togglePassword');
                
                if (passwordInput.type === 'password') {{
                    passwordInput.type = 'text';
                    toggleBtn.textContent = '🙈';
                }} else {{
                    passwordInput.type = 'password';
                    toggleBtn.textContent = '👁️';
                }}
            }}
        </script>
    </head>
    <body class="auth-bg">
        <div class="auth-card">
            <div class="auth-logo-icon">📖</div>
            <h2 class="auth-title">Welcome Back</h2>
            <p class="auth-subtitle">Sign in to continue writing your story</p>
            
            <div class="flash-messages">{flash_messages}</div>
            
            <form method="POST">
                <div class="input-group">
                    <span class="icon">👤</span>
                    <input type="text" name="username" placeholder="Username" required>
                </div>
                <div class="input-group">
                    <span class="icon">🔒</span>
                    <input type="password" id="password" name="password" placeholder="Password" required>
                    <button type="button" class="password-toggle" id="togglePassword" onclick="togglePassword()">👁️</button>
                </div>
                <button type="submit" class="btn-auth-primary">Sign In</button>
            </form>
            
            <div style="margin-top: 20px; font-size: 11px; color: #a0aec0;">
                <p>Demo Accounts:</p>
                <p>Alex / Ade / Yemi</p>
                <p>Password: Password@123</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_flashed_messages():
    """Get flash messages from session"""
    messages = session.pop('_flashes', [])
    return messages

# ==============================================================================
# DASHBOARD
# ==============================================================================

@app.route("/")
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("settings"))

# ==============================================================================
# SETTINGS ROUTES (Simplified - All work with SQLite)
# ==============================================================================

@app.route("/settings")
def settings():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user = session["user"]
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT display_name, avatar FROM profiles WHERE username = ?", (user,))
    profile = cursor.fetchone()
    conn.close()
    
    display_name = profile["display_name"] if profile else user
    avatar_url = profile["avatar"] if profile else ""

    content = f"""
    <div class="settings-header">
        <div>
            <h1>Settings</h1>
            <p>Customize your journal experience 💜</p>
        </div>
        <div style="display: flex; align-items: center; gap: 10px; background: #faf9fc; padding: 6px 12px; border-radius: 20px; border: 1px solid #f0edf5;">
            <img src="{avatar_url}" style="width:28px; height:28px; border-radius:50%; object-fit:cover;">
            <span style="font-size: 12px; font-weight: 600;">{display_name}</span>
        </div>
    </div>

    <div class="settings-list">
        <a href="/settings/profile" class="settings-item">
            <div class="settings-left">
                <div class="icon-box icon-purple">👤</div>
                <div class="settings-info">
                    <h3>Profile Settings</h3>
                    <p>Manage avatar, display name, bio, email, and personal details.</p>
                </div>
            </div>
            <span>›</span>
        </a>
        <a href="/settings/notifications" class="settings-item">
            <div class="settings-left">
                <div class="icon-box icon-yellow">🔔</div>
                <div class="settings-info">
                    <h3>Notification Preferences</h3>
                    <p>Daily reminders, push & email alerts, streaks, and quiet hours.</p>
                </div>
            </div>
            <span>›</span>
        </a>
        <a href="/settings/privacy" class="settings-item">
            <div class="settings-left">
                <div class="icon-box icon-green">🛡️</div>
                <div class="settings-info">
                    <h3>Privacy Options</h3>
                    <p>Passcode/Face ID lock, default entry privacy, and encryption.</p>
                </div>
            </div>
            <span>›</span>
        </a>
        <a href="/settings/theme" class="settings-item">
            <div class="settings-left">
                <div class="icon-box icon-blue">🖌️</div>
                <div class="settings-info">
                    <h3>Theme Customization</h3>
                    <p>Light/Dark mode, color presets, typography, and background textures.</p>
                </div>
            </div>
            <span>›</span>
        </a>
        <a href="/settings/backup" class="settings-item">
            <div class="settings-left">
                <div class="icon-box icon-amber">☁️</div>
                <div class="settings-info">
                    <h3>Backup & Sync</h3>
                    <p>Cloud synchronization, manual backups, and restore choices.</p>
                </div>
            </div>
            <span>›</span>
        </a>
        <a href="/settings/account" class="settings-item">
            <div class="settings-left">
                <div class="icon-box icon-pink">🔒</div>
                <div class="settings-info">
                    <h3>Account Management</h3>
                    <p>Security credentials, active sessions, subscriptions, and data deletion.</p>
                </div>
            </div>
            <span>›</span>
        </a>
    </div>
    """
    return layout(content)

# ==============================================================================
# PROFILE SETTINGS
# ==============================================================================

@app.route("/settings/profile", methods=["GET", "POST"])
def profile_settings():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user = session["user"]
    msg = ""
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == "POST":
        display_name = request.form.get("display_name", user)
        bio = request.form.get("bio", "")
        avatar = request.form.get("avatar_url", "")
        dob = request.form.get("dob", "")
        timezone = request.form.get("timezone", "")
        email = request.form.get("email", "")
        
        # Update profile
        cursor.execute(
            "UPDATE profiles SET display_name = ?, bio = ?, avatar = ?, dob = ?, timezone = ?, updated_at = ? WHERE username = ?",
            (display_name, bio, avatar, dob, timezone, datetime.now().isoformat(), user)
        )
        
        # Update email in users table
        cursor.execute(
            "UPDATE users SET email = ? WHERE username = ?",
            (email, user)
        )
        
        conn.commit()
        msg = "Profile updated successfully! ✨"
    
    # Get fresh data
    cursor.execute("SELECT * FROM profiles WHERE username = ?", (user,))
    profile = cursor.fetchone()
    
    cursor.execute("SELECT email FROM users WHERE username = ?", (user,))
    user_data = cursor.fetchone()
    conn.close()
    
    content = f"""
    <div style="margin-bottom: 20px;">
        <a href="/settings" style="text-decoration: none; color: #8c8c9a; font-size: 11px;">← Back to Settings</a>
        <h1 style="font-family: Georgia, serif; font-size: 22px; color: #2d2a32; margin-top: 6px;">Profile Settings</h1>
    </div>
    {'<p class="success-msg">' + msg + '</p>' if msg else ''}
    <div class="profile-card">
        <form method="POST">
            <div class="profile-section-title">🖼️ Profile Picture</div>
            <div class="field-box">
                <label class="field-label">AVATAR URL</label>
                <input type="url" name="avatar_url" class="field-input" value="{profile['avatar'] if profile else ''}">
            </div>
            
            <div class="profile-section-title">👤 Basic Information</div>
            <div class="form-grid-2">
                <div class="field-box">
                    <label class="field-label">DISPLAY NAME</label>
                    <input type="text" name="display_name" class="field-input" value="{profile['display_name'] if profile else user}">
                </div>
                <div class="field-box">
                    <label class="field-label">USERNAME</label>
                    <input type="text" class="field-input" value="{user}" disabled style="opacity:0.7;">
                </div>
            </div>
            <div class="field-box">
                <label class="field-label">BIO / QUOTE</label>
                <textarea name="bio" class="field-input" rows="2">{profile['bio'] if profile else ''}</textarea>
            </div>

            <div class="profile-section-title">✉️ Contact Information</div>
            <div class="field-box">
                <label class="field-label">EMAIL</label>
                <input type="email" name="email" class="field-input" value="{user_data['email'] if user_data else ''}">
            </div>

            <div class="profile-section-title">🗓️ Personal Details</div>
            <div class="form-grid-2">
                <div class="field-box">
                    <label class="field-label">DATE OF BIRTH</label>
                    <input type="date" name="dob" class="field-input" value="{profile['dob'] if profile else ''}">
                </div>
                <div class="field-box">
                    <label class="field-label">TIME ZONE</label>
                    <input type="text" name="timezone" class="field-input" value="{profile['timezone'] if profile else ''}">
                </div>
            </div>
            <div class="profile-form-footer">
                <button type="submit" class="btn-primary">Save Changes</button>
            </div>
        </form>
    </div>
    """
    return layout(content)

# ==============================================================================
# NOTIFICATION SETTINGS
# ==============================================================================

@app.route("/settings/notifications", methods=["GET", "POST"])
def notification_settings():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user = session["user"]
    settings = get_user_settings(user)
    st = settings["notifications"] if settings else {}
    msg = ""
    
    if request.method == "POST":
        st["daily_reminder"] = "daily_reminder" in request.form
        st["reminder_time"] = request.form.get("reminder_time", "20:00")
        st["reminder_freq"] = request.form.get("reminder_freq", "Daily")
        st["push_enabled"] = "push_enabled" in request.form        st["email_summaries"] = "email_summaries" in request.form
        st["streak_alerts"] = "streak_alerts" in request.form
        st["security_alerts"] = "security_alerts" in request.form
        st["quiet_hours"] = "quiet_hours" in request.form
        st["quiet_start"] = request.form.get("quiet_start", "22:00")
        st["quiet_end"] = request.form.get("quiet_end", "07:00")
        
        update_setting(user, "notifications", st)
        msg = "Notification preferences saved! 🔔"
    
    content = f"""
    <div style="margin-bottom: 20px;">
        <a href="/settings" style="text-decoration: none; color: #8c8c9a; font-size: 11px;">← Back to Settings</a>
        <h1 style="font-family: Georgia, serif; font-size: 22px; color: #2d2a32; margin-top: 6px;">Notification Preferences</h1>
    </div>
    {'<p class="success-msg">' + msg + '</p>' if msg else ''}
    <div class="profile-card">
        <form method="POST">
            <div class="profile-section-title">⏰ 1. Daily Journaling Reminders</div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Enable Daily Reminders</div>
                    <div class="toggle-desc">Get nudged when it's time to reflect</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="daily_reminder" {'checked' if st.get('daily_reminder', True) else ''}>
                    <span class="slider"></span>
                </label>
            </div>
            <div class="form-grid-2">
                <div class="field-box">
                    <label class="field-label">PREFERRED TIME</label>
                    <input type="time" name="reminder_time" class="field-input" value="{st.get('reminder_time', '20:00')}">
                </div>
                <div class="field-box">
                    <label class="field-label">FREQUENCY</label>
                    <select name="reminder_freq" class="field-input">
                        <option {'selected' if st.get('reminder_freq') == 'Daily' else ''}>Daily</option>
                        <option {'selected' if st.get('reminder_freq') == 'Weekdays Only' else ''}>Weekdays Only</option>
                        <option {'selected' if st.get('reminder_freq') == 'Weekends Only' else ''}>Weekends Only</option>
                    </select>
                </div>
            </div>

            <div class="profile-section-title">📡 2. Delivery Channels</div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Push Notifications</div>
                    <div class="toggle-desc">Instant alerts on phone and browser</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="push_enabled" {'checked' if st.get('push_enabled', True) else ''}>
                    <span class="slider"></span>
                </label>
            </div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Email Summaries</div>
                    <div class="toggle-desc">Weekly or monthly digest of entries</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="email_summaries" {'checked' if st.get('email_summaries', False) else ''}>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="profile-section-title">🔥 3. Streak & Goal Alerts</div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Streak Warnings & Milestones</div>
                    <div class="toggle-desc">Alerts when near breaking a writing streak</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="streak_alerts" {'checked' if st.get('streak_alerts', True) else ''}>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="profile-section-title">🛡️ 4. Account & Security Alerts</div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Login & Backup Alerts</div>
                    <div class="toggle-desc">Security notifications for new sign-ins</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="security_alerts" {'checked' if st.get('security_alerts', True) else ''}>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="profile-section-title">🌙 5. Quiet Hours / Do Not Disturb</div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Enable Quiet Mode</div>
                    <div class="toggle-desc">Mute all reminders during sleep hours</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="quiet_hours" {'checked' if st.get('quiet_hours', True) else ''}>
                    <span class="slider"></span>
                </label>
            </div>
            <div class="form-grid-2">
                <div class="field-box">
                    <label class="field-label">START TIME</label>
                    <input type="time" name="quiet_start" class="field-input" value="{st.get('quiet_start', '22:00')}">
                </div>
                <div class="field-box">
                    <label class="field-label">END TIME</label>
                    <input type="time" name="quiet_end" class="field-input" value="{st.get('quiet_end', '07:00')}">
                </div>
            </div>

            <div class="profile-form-footer">
                <button type="submit" class="btn-primary">Save Preferences</button>
            </div>
        </form>
    </div>
    """
    return layout(content)

# ==============================================================================
# PRIVACY SETTINGS
# ==============================================================================

@app.route("/settings/privacy", methods=["GET", "POST"])
def privacy_settings():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user = session["user"]
    settings = get_user_settings(user)
    st = settings["privacy"] if settings else {}
    msg = ""
    
    if request.method == "POST":
        st["passcode_enabled"] = "passcode_enabled" in request.form
        st["biometric_enabled"] = "biometric_enabled" in request.form
        st["auto_lock"] = request.form.get("auto_lock", "1min")
        st["default_private"] = "default_private" in request.form
        st["hide_previews"] = "hide_previews" in request.form
        st["blur_app"] = "blur_app" in request.form
        st["e2ee"] = "e2ee" in request.form
        st["analytics"] = "analytics" in request.form
        
        update_setting(user, "privacy", st)
        msg = "Privacy settings saved! 🛡️"
    
    content = f"""
    <div style="margin-bottom: 20px;">
        <a href="/settings" style="text-decoration: none; color: #8c8c9a; font-size: 11px;">← Back to Settings</a>
        <h1 style="font-family: Georgia, serif; font-size: 22px; color: #2d2a32; margin-top: 6px;">Privacy Options</h1>
    </div>
    {'<p class="success-msg">' + msg + '</p>' if msg else ''}
    <div class="profile-card">
        <form method="POST">
            <div class="profile-section-title">🔑 1. App Lock & Biometrics</div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Passcode Lock</div>
                    <div class="toggle-desc">Require PIN to open journal</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="passcode_enabled" {'checked' if st.get('passcode_enabled', False) else ''}>
                    <span class="slider"></span>
                </label>
            </div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Face ID / Fingerprint Auth</div>
                    <div class="toggle-desc">Biometric unlock enabled</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="biometric_enabled" {'checked' if st.get('biometric_enabled', True) else ''}>
                    <span class="slider"></span>
                </label>
            </div>
            <div class="field-box">
                <label class="field-label">AUTO-LOCK DELAY</label>
                <select name="auto_lock" class="field-input">
                    <option value="Immediately" {'selected' if st.get('auto_lock') == 'Immediately' else ''}>Immediately</option>
                    <option value="1min" {'selected' if st.get('auto_lock') == '1min' else ''}>After 1 Minute</option>
                    <option value="5min" {'selected' if st.get('auto_lock') == '5min' else ''}>After 5 Minutes</option>
                </select>
            </div>

            <div class="profile-section-title">👁️ 2. Entry Visibility & Default Privacy</div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Default Private Status</div>
                    <div class="toggle-desc">New entries are strictly private</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="default_private" {'checked' if st.get('default_private', True) else ''}>
                    <span class="slider"></span>
                </label>
            </div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Hide Entry Previews</div>
                    <div class="toggle-desc">Hide text snippets on dashboard</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="hide_previews" {'checked' if st.get('hide_previews', False) else ''}>
                    <span class="slider"></span>
                </label>
            </div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Blur Screen in Multitasking</div>
                    <div class="toggle-desc">Blurs app when switching apps</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="blur_app" {'checked' if st.get('blur_app', True) else ''}>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="profile-section-title">🔐 3. Data Encryption</div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">End-to-End Encryption (E2EE)</div>
                    <div class="toggle-desc">Encrypted before syncing to server</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="e2ee" {'checked' if st.get('e2ee', True) else ''}>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="profile-section-title">🤖 4. Data Sharing & AI Privacy</div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Anonymous Analytics</div>
                    <div class="toggle-desc">Send diagnostic reports</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="analytics" {'checked' if st.get('analytics', False) else ''}>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="profile-form-footer">
                <button type="submit" class="btn-primary">Save Privacy Options</button>
            </div>
        </form>
    </div>
    """
    return layout(content)

# ==============================================================================
# THEME SETTINGS
# ==============================================================================

@app.route("/settings/theme", methods=["GET", "POST"])
def theme_settings():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user = session["user"]
    settings = get_user_settings(user)
    st = settings["theme"] if settings else {}
    msg = ""
    
    if request.method == "POST":
        st["mode"] = request.form.get("mode", "Light")
        st["preset"] = request.form.get("preset", "Pastel Lavender")
        st["accent_color"] = request.form.get("accent_color", "#8e7cc3")
        st["font_style"] = request.form.get("font_style", "Georgia")
        st["font_size"] = request.form.get("font_size", "Medium")
        st["texture"] = request.form.get("texture", "Plain White")
        st["layout"] = request.form.get("layout", "Standard")
        
        update_setting(user, "theme", st)
        msg = "Theme customization saved! 🎨"
    
    content = f"""
    <div style="margin-bottom: 20px;">
        <a href="/settings" style="text-decoration: none; color: #8c8c9a; font-size: 11px;">← Back to Settings</a>
        <h1 style="font-family: Georgia, serif; font-size: 22px; color: #2d2a32; margin-top: 6px;">Theme Customization</h1>
    </div>
    {'<p class="success-msg">' + msg + '</p>' if msg else ''}
    <div class="profile-card">
        <form method="POST">
            <div class="profile-section-title">🌓 1. Appearance Mode</div>
            <div class="field-box">
                <label class="field-label">MODE</label>
                <select name="mode" class="field-input">
                    <option {'selected' if st.get('mode') == 'Light' else ''}>Light</option>
                    <option {'selected' if st.get('mode') == 'Dark' else ''}>Dark</option>
                    <option {'selected' if st.get('mode') == 'Auto System' else ''}>Auto System</option>
                </select>
            </div>

            <div class="profile-section-title">🎨 2. Accent & Palette Colors</div>
            <div class="form-grid-2">
                <div class="field-box">
                    <label class="field-label">PRESET PALETTE</label>
                    <select name="preset" class="field-input">
                        <option {'selected' if st.get('preset') == 'Pastel Lavender' else ''}>Pastel Lavender</option>
                        <option {'selected' if st.get('preset') == 'Forest Green' else ''}>Forest Green</option>
                        <option {'selected' if st.get('preset') == 'Warm Sunset' else ''}>Warm Sunset</option>
                        <option {'selected' if st.get('preset') == 'Minimalist Charcoal' else ''}>Minimalist Charcoal</option>
                    </select>
                </div>
                <div class="field-box">
                    <label class="field-label">ACCENT COLOR</label>
                    <input type="color" name="accent_color" class="field-input" value="{st.get('accent_color', '#8e7cc3')}" style="height:38px; padding:2px;">
                </div>
            </div>

            <div class="profile-section-title">🔤 3. Typography & Text Options</div>
            <div class="form-grid-2">
                <div class="field-box">
                    <label class="field-label">FONT FAMILY</label>
                    <select name="font_style" class="field-input">
                        <option {'selected' if st.get('font_style') == 'Georgia' else ''}>Georgia (Serif)</option>
                        <option {'selected' if st.get('font_style') == 'Sans-Serif' else ''}>Sans-Serif (Modern)</option>
                        <option {'selected' if st.get('font_style') == 'Handwritten' else ''}>Handwritten</option>
                    </select>
                </div>
                <div class="field-box">
                    <label class="field-label">TEXT SIZE</label>
                    <select name="font_size" class="field-input">
                        <option {'selected' if st.get('font_size') == 'Small' else ''}>Small</option>
                        <option {'selected' if st.get('font_size') == 'Medium' else ''}>Medium</option>
                        <option {'selected' if st.get('font_size') == 'Large' else ''}>Large</option>
                    </select>
                </div>
            </div>

            <div class="profile-section-title">📄 4. Background & Atmosphere</div>
            <div class="form-grid-2">
                <div class="field-box">
                    <label class="field-label">JOURNAL TEXTURE</label>
                    <select name="texture" class="field-input">
                        <option {'selected' if st.get('texture') == 'Plain White' else ''}>Plain White</option>
                        <option {'selected' if st.get('texture') == 'Lined Paper' else ''}>Lined Paper</option>
                        <option {'selected' if st.get('texture') == 'Dot Grid' else ''}>Dot Grid</option>
                    </select>
                </div>
                <div class="field-box">
                    <label class="field-label">LAYOUT DENSITY</label>
                    <select name="layout" class="field-input">
                        <option {'selected' if st.get('layout') == 'Standard' else ''}>Standard</option>
                        <option {'selected' if st.get('layout') == 'Compact' else ''}>Compact</option>
                    </select>
                </div>
            </div>

            <div class="profile-form-footer">
                <button type="submit" class="btn-primary">Apply Theme</button>
            </div>
        </form>
    </div>
    """
    return layout(content)

# ==============================================================================
# BACKUP SETTINGS
# ==============================================================================

@app.route("/settings/backup", methods=["GET", "POST"])
def backup_settings():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user = session["user"]
    settings = get_user_settings(user)
    st = settings["backup"] if settings else {}
    msg = ""
    
    if request.method == "POST":
        if "action_backup_now" in request.form:
            st["last_backup"] = datetime.now().strftime("%b %d, %Y %I:%M %p")
            update_setting(user, "backup", st)
            msg = "Manual backup completed successfully! ☁️"
        else:
            st["auto_sync"] = "auto_sync" in request.form
            st["sync_freq"] = request.form.get("sync_freq", "Daily")
            st["network"] = request.form.get("network", "Wi-Fi Only")
            st["destination"] = request.form.get("destination", "App Cloud")
            update_setting(user, "backup", st)
            msg = "Backup settings updated! ☁️"
    
    content = f"""
    <div style="margin-bottom: 20px;">
        <a href="/settings" style="text-decoration: none; color: #8c8c9a; font-size: 11px;">← Back to Settings</a>
        <h1 style="font-family: Georgia, serif; font-size: 22px; color: #2d2a32; margin-top: 6px;">Backup & Sync</h1>
    </div>
    {'<p class="success-msg">' + msg + '</p>' if msg else ''}
    <div class="profile-card">
        <form method="POST">
            <div class="profile-section-title">☁️ 1. Cloud Sync Settings</div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Auto-Sync Entries</div>
                    <div class="toggle-desc">Automatically keep entries in cloud</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="auto_sync" {'checked' if st.get('auto_sync', True) else ''}>
                    <span class="slider"></span>
                </label>
            </div>
            <div class="form-grid-2">
                <div class="field-box">
                    <label class="field-label">SYNC FREQUENCY</label>
                    <select name="sync_freq" class="field-input">
                        <option {'selected' if st.get('sync_freq') == 'Real-time' else ''}>Real-time</option>
                        <option {'selected' if st.get('sync_freq') == 'Daily' else ''}>Daily</option>
                        <option {'selected' if st.get('sync_freq') == 'On App Launch' else ''}>On App Launch</option>
                    </select>
                </div>
                <div class="field-box">
                    <label class="field-label">NETWORK PREFERENCE</label>
                    <select name="network" class="field-input">
                        <option {'selected' if st.get('network') == 'Wi-Fi Only' else ''}>Wi-Fi Only</option>
                        <option {'selected' if st.get('network') == 'Wi-Fi & Cellular' else ''}>Wi-Fi & Cellular</option>
                    </select>
                </div>
            </div>

            <div class="profile-section-title">📦 2. Manual Backup & Status</div>
            <div style="background:#faf9fc; border:1px solid #f2f0f7; padding:15px; border-radius:12px; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:12px; font-weight:600;">Last Successful Backup</div>
                    <div style="font-size:10px; color:#928e9c;">{st.get('last_backup', 'Never')}</div>
                </div>
                <button type="submit" name="action_backup_now" value="true" class="btn-secondary">Back Up Now</button>
            </div>

            <div class="profile-section-title">🌐 3. Cloud Provider Choice</div>
            <div class="field-box">
                <label class="field-label">DESTINATION</label>
                <select name="destination" class="field-input">
                    <option {'selected' if st.get('destination') == 'App Cloud' else ''}>App Cloud (Encrypted)</option>
                    <option {'selected' if st.get('destination') == 'Google Drive' else ''}>Google Drive</option>
                    <option {'selected' if st.get('destination') == 'iCloud' else ''}>iCloud</option>
                </select>
            </div>

            <div class="profile-form-footer">
                <button type="submit" class="btn-primary">Save Backup Settings</button>
            </div>
        </form>
    </div>
    """
    return layout(content)

# ==============================================================================
# ACCOUNT SETTINGS
# ==============================================================================

@app.route("/settings/account", methods=["GET", "POST"])
def account_settings():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user = session["user"]
    settings = get_user_settings(user)
    st = settings["account"] if settings else {}
    msg = ""
    error = ""
    
    if request.method == "POST":
        if "action_change_pass" in request.form:
            old = request.form.get("old_pass", "")
            new = request.form.get("new_pass", "")
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (user,))
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data and check_password_hash(user_data["password"], old):
                valid, pass_msg = is_strong_password(new)
                if valid:
                    hashed = generate_password_hash(new)
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed, user))
                    conn.commit()
                    conn.close()
                    msg = "Password changed successfully! 🔑"
                else:
                    error = pass_msg
            else:
                error = "Incorrect current password."
        else:
            st["2fa_enabled"] = "2fa_enabled" in request.form
            update_setting(user, "account", st)
            msg = "Account management settings updated! 🔒"
    
    content = f"""
    <div style="margin-bottom: 20px;">
        <a href="/settings" style="text-decoration: none; color: #8c8c9a; font-size: 11px;">← Back to Settings</a>
        <h1 style="font-family: Georgia, serif; font-size: 22px; color: #2d2a32; margin-top: 6px;">Account Management</h1>
    </div>
    {'<p class="success-msg">' + msg + '</p>' if msg else ''}
    {'<p class="error-msg">' + error + '</p>' if error else ''}
    <div class="profile-card">
        <form method="POST">
            <div class="profile-section-title">🔐 1. Security Credentials</div>
            <div class="toggle-row">
                <div>
                    <div class="toggle-title">Two-Factor Authentication (2FA)</div>
                    <div class="toggle-desc">Extra security for sign-in</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="2fa_enabled" {'checked' if st.get('2fa_enabled', False) else ''}>
                    <span class="slider"></span>
                </label>
            </div>

            <div class="profile-section-title">💎 2. Subscription Plan</div>
            <div style="background:#faf9fc; border:1px solid #f2f0f7; padding:12px; border-radius:12px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:12px; font-weight:600;">Current Tier: {st.get('plan', 'Journal Free')}</div>
                    <div style="font-size:10px; color:#928e9c;">Storage: {st.get('storage_used', '0.1 GB of 1.0 GB')}</div>
                </div>
                <button type="button" class="btn-secondary">Manage Plan</button>
            </div>

            <div class="profile-form-footer">
                <button type="submit" class="btn-primary">Save Settings</button>
            </div>
        </form>

        <hr style="border:none; border-top:1px solid #f2f0f7; margin:22px 0;">

        <form method="POST">
            <input type="hidden" name="action_change_pass" value="true">
            <div class="profile-section-title">🔑 Update Password</div>
            <div class="form-grid-2">
                <div class="field-box">
                    <label class="field-label">CURRENT PASSWORD</label>
                    <input type="password" name="old_pass" class="field-input" required>
                </div>
                <div class="field-box">
                    <label class="field-label">NEW PASSWORD</label>
                    <input type="password" name="new_pass" class="field-input" required>
                </div>
            </div>
            <div class="profile-form-footer">
                <button type="submit" class="btn-primary">Update Password</button>
            </div>
        </form>
    </div>
    """
    return layout(content)

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)