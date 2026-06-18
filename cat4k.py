#!/usr/bin/env python3.14
# -*- coding: utf-8 -*-
# import python 3.14 files = off
# pr
"""
CAT CLIENT 1.0 (Fixed for Python 3.14+)
[C] SAMSOFT 2025 - CRACKED/OFFLINE MODE SUPPORT
DARK/LIGHT/SYSTEM THEME TOGGLE
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import urllib.request
import subprocess
import zipfile
import ssl
import threading
import sys
import os
import platform
from pathlib import Path
import uuid
import io
import hashlib
import concurrent.futures

# Create an explicit unverified context to use directly in urlopen
ctx = ssl._create_unverified_context()

# Paths
if sys.platform == "win32":
    GAME_DIR = Path.home() / "AppData" / "Roaming" / ".minecraft"
elif sys.platform == "darwin":
    GAME_DIR = Path.home() / "Library" / "Application Support" / "minecraft"
else:
    GAME_DIR = Path.home() / ".minecraft"

SKIN_SERVER = "https://mc-heads.net"
VERSION_MANIFEST_URLS = [
    "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json",
    "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json",
]
ASSETS_URL = "https://resources.download.minecraft.net"
CLASSPATH_SEP = ";" if sys.platform == "win32" else ":"
USER_AGENT = "CatClient/1.0"
DOWNLOAD_CHUNK = 1024 * 1024
LIB_WORKERS = 32
ASSET_WORKERS = 48

# ============== CAT CLIENT THEMES ==============
THEMES = {
    "dark": {
        "bg_dark": "#1a1a2e",
        "bg_darker": "#16213e",
        "bg_panel": "#1f2937",
        "bg_input": "#374151",
        "bg_header": "#7c3aed",
        "accent": "#a78bfa",
        "accent_hover": "#c4b5fd",
        "accent_green": "#10b981",
        "accent_green_hover": "#34d399",
        "accent_orange": "#f59e0b",
        "accent_blue": "#3b82f6",
        "text_primary": "#ffffff",
        "text_secondary": "#9ca3af",
        "text_muted": "#6b7280",
        "border": "#374151",
        "button_play": "#1f2937",
        "button_play_hover": "#374151",
        "button_play_text": "#ffffff",
    },
    "light": {
        "bg_dark": "#f3f4f6",
        "bg_darker": "#e5e7eb",
        "bg_panel": "#ffffff",
        "bg_input": "#f9fafb",
        "bg_header": "#8b5cf6",
        "accent": "#7c3aed",
        "accent_hover": "#6d28d9",
        "accent_green": "#059669",
        "accent_green_hover": "#047857",
        "accent_orange": "#d97706",
        "accent_blue": "#2563eb",
        "text_primary": "#111827",
        "text_secondary": "#4b5563",
        "text_muted": "#9ca3af",
        "border": "#d1d5db",
        "button_play": "#111827",
        "button_play_hover": "#1f2937",
        "button_play_text": "#ffffff",
    }
}

# ============== UTILITY FUNCTIONS ==============
def get_system_theme():
    """Detect system dark/light mode"""
    try:
        if sys.platform == "win32":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value else "dark"
        elif sys.platform == "darwin":
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True
            )
            return "dark" if "Dark" in result.stdout else "light"
    except:
        pass
    return "dark"


def find_java():
    candidates = []
    java_home = os.environ.get("JAVA_HOME", "").strip()
    if sys.platform == "win32":
        if java_home:
            candidates.append(Path(java_home) / "bin" / "java.exe")
        candidates.extend([
            Path("C:/Program Files/Java/jdk-17/bin/java.exe"),
            Path("C:/Program Files/Java/jdk-21/bin/java.exe"),
            Path("C:/Program Files/Eclipse Adoptium/jdk-17/bin/java.exe"),
            Path("C:/Program Files/Eclipse Adoptium/jdk-21/bin/java.exe"),
            Path("C:/Program Files/BellSoft/LibericaJDK-21/bin/java.exe"),
            Path("C:/Program Files/BellSoft/LibericaJDK-17/bin/java.exe"),
        ])
    elif sys.platform == "darwin":
        if java_home:
            candidates.append(Path(java_home) / "bin" / "java")
        candidates.extend([
            Path("/opt/homebrew/opt/openjdk@17/bin/java"),
            Path("/opt/homebrew/opt/openjdk@21/bin/java"),
            Path("/opt/homebrew/opt/openjdk/bin/java"),
            Path("/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home/bin/java"),
            Path("/usr/bin/java"),
        ])
    else:
        if java_home:
            candidates.append(Path(java_home) / "bin" / "java")
        candidates.extend([
            Path("/usr/lib/jvm/java-17-openjdk/bin/java"),
            Path("/usr/lib/jvm/java-17-openjdk-amd64/bin/java"),
            Path("/usr/bin/java"),
        ])
    
    for path in candidates:
        if path.exists():
            return str(path)
    return "java"


def get_os_name():
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "osx"
    return "linux"


def get_arch():
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "x64"
    elif machine in ("aarch64", "arm64"):
        return "arm64"
    return "x86"


def check_rules(rules):
    if not rules:
        return True
    
    os_name = get_os_name()
    arch = get_arch()
    result = False
    
    for rule in rules:
        action = rule.get("action", "allow")
        matches = True
        
        if "os" in rule:
            os_rule = rule["os"]
            if "name" in os_rule and os_rule["name"] != os_name:
                matches = False
            if "arch" in os_rule and os_rule["arch"] != arch:
                matches = False
        
        if matches:
            result = (action == "allow")
    
    return result


def check_arg_rules(rules, features=None):
    """Evaluate Mojang argument rules (OS + feature flags)."""
    if not rules:
        return True
    features = features or {}
    result = False
    for rule in rules:
        action = rule.get("action", "allow")
        matches = True
        if "os" in rule:
            os_rule = rule["os"]
            if "name" in os_rule and os_rule["name"] != get_os_name():
                matches = False
            if "arch" in os_rule and os_rule["arch"] != get_arch():
                matches = False
        if "features" in rule:
            for feat, required in rule["features"].items():
                if features.get(feat, False) != required:
                    matches = False
                    break
        if matches:
            result = (action == "allow")
    return result


def substitute_vars(text, variables):
    if not isinstance(text, str):
        return text
    for key, value in variables.items():
        text = text.replace("${" + key + "}", str(value))
    return text


def expand_arguments(arg_list, variables, features=None):
    """Expand version.json JVM/game argument lists."""
    expanded = []
    for entry in arg_list:
        if isinstance(entry, str):
            expanded.append(substitute_vars(entry, variables))
        elif isinstance(entry, dict):
            if not check_arg_rules(entry.get("rules"), features):
                continue
            value = entry.get("value", "")
            if isinstance(value, list):
                for item in value:
                    expanded.append(substitute_vars(item, variables))
            elif value:
                expanded.append(substitute_vars(value, variables))
    return expanded


def generate_offline_uuid(username):
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, f"OfflinePlayer:{username}"))


def calculate_sha1(filepath):
    sha1 = hashlib.sha1()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(65536):
                sha1.update(chunk)
        return sha1.hexdigest()
    except OSError:
        return None


def fetch_json(url, timeout=15):
    """Fetch JSON over HTTPS with explicit SSL context."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode())


def fetch_version_manifest(timeout=15):
    """Try current Mojang manifest endpoints in order."""
    last_err = None
    for url in VERSION_MANIFEST_URLS:
        try:
            return fetch_json(url, timeout=timeout)
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"Could not fetch version manifest: {last_err}")


def file_is_valid(dest_path, expected_hash=None, expected_size=None):
    """Fast local cache check — size first, SHA1 only when needed."""
    dest_path = Path(dest_path)
    if not dest_path.exists():
        return False
    try:
        actual_size = dest_path.stat().st_size
    except OSError:
        return False
    if expected_size is not None and actual_size != expected_size:
        return False
    if expected_hash:
        if dest_path.name == expected_hash and expected_size is not None:
            return True
        return calculate_sha1(dest_path) == expected_hash
    return True


def download_file_fast(url, dest_path, expected_hash=None, expected_size=None, timeout=60):
    """Stream download with cache skip and optional integrity check."""
    dest_path = Path(dest_path)
    tmp_path = dest_path.with_suffix(dest_path.suffix + ".part")
    if file_is_valid(dest_path, expected_hash, expected_size):
        return True
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            with open(tmp_path, "wb") as f:
                while True:
                    chunk = resp.read(DOWNLOAD_CHUNK)
                    if not chunk:
                        break
                    f.write(chunk)
        if expected_hash and calculate_sha1(tmp_path) != expected_hash:
            tmp_path.unlink(missing_ok=True)
            return False
        if expected_size is not None and tmp_path.stat().st_size != expected_size:
            tmp_path.unlink(missing_ok=True)
            return False
        tmp_path.replace(dest_path)
        return True
    except Exception as exc:
        print(f"Download failed ({dest_path.name}): {exc}")
        tmp_path.unlink(missing_ok=True)
        return False


# ============== ASSET DOWNLOADER ==============
class AssetDownloader:
    def __init__(self, game_dir, progress_callback=None, status_callback=None):
        self.game_dir = Path(game_dir)
        self.assets_dir = self.game_dir / "assets"
        self.objects_dir = self.assets_dir / "objects"
        self.indexes_dir = self.assets_dir / "indexes"
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.downloaded = 0
        self.total = 0
        self.failed = []
        self._lock = threading.Lock()
    
    def download_file(self, url, dest_path, expected_hash=None, expected_size=None):
        return download_file_fast(url, dest_path, expected_hash, expected_size, timeout=30)
    
    def download_asset(self, asset_hash, asset_size=None):
        prefix = asset_hash[:2]
        asset_path = self.objects_dir / prefix / asset_hash
        url = f"{ASSETS_URL}/{prefix}/{asset_hash}"
        
        success = self.download_file(url, asset_path, asset_hash, asset_size)
        
        with self._lock:
            self.downloaded += 1
            progress = int((self.downloaded / self.total) * 100) if self.total else 0
        if self.progress_callback and self.total > 0:
            self.progress_callback(progress)
        
        if not success:
            self.failed.append(asset_hash)
        
        return success
    
    def download_all_assets(self, asset_index_id, asset_index_url=None):
        self.objects_dir.mkdir(parents=True, exist_ok=True)
        self.indexes_dir.mkdir(parents=True, exist_ok=True)
        
        index_path = self.indexes_dir / f"{asset_index_id}.json"
        if not index_path.exists() and asset_index_url:
            if self.status_callback:
                self.status_callback("Downloading asset index...")
            self.download_file(asset_index_url, index_path)
        
        if not index_path.exists():
            raise FileNotFoundError(f"Asset index not found: {index_path}")
        
        with open(index_path) as f:
            asset_index = json.load(f)
        
        objects = asset_index.get("objects", {})
        self.total = len(objects)
        self.downloaded = 0
        self.failed = []
        
        if self.status_callback:
            self.status_callback(f"Checking {self.total} assets...")
        
        assets_to_download = []
        for asset_name, asset_info in objects.items():
            asset_hash = asset_info["hash"]
            asset_size = asset_info.get("size")
            prefix = asset_hash[:2]
            asset_path = self.objects_dir / prefix / asset_hash
            
            if file_is_valid(asset_path, asset_hash, asset_size):
                self.downloaded += 1
                continue
            
            assets_to_download.append((asset_hash, asset_size))
        
        if self.status_callback:
            self.status_callback(f"Downloading {len(assets_to_download)} assets...")
        
        if assets_to_download:
            with concurrent.futures.ThreadPoolExecutor(max_workers=ASSET_WORKERS) as executor:
                list(executor.map(lambda item: self.download_asset(*item), assets_to_download))
        
        if self.status_callback:
            if self.failed:
                self.status_callback(f"Assets done ({len(self.failed)} failed)")
            else:
                self.status_callback("All assets downloaded!")
        
        return len(self.failed) == 0


# ============== THEME TOGGLE WIDGET ==============
class ThemeToggle(tk.Frame):
    def __init__(self, parent, callback, initial="system", **kwargs):
        super().__init__(parent, **kwargs)
        self.callback = callback
        self.current = initial
        self.options = ["dark", "light", "system"]
        self.labels = ["🌙", "☀️", "💻"]
        
        self.configure(bg=kwargs.get("bg", "#16213e"))
        
        self.buttons = []
        for i, (opt, lbl) in enumerate(zip(self.options, self.labels)):
            btn = tk.Label(
                self, text=lbl, font=("Segoe UI", 12),
                fg="#ffffff" if opt == initial else "#6b7280",
                bg=self["bg"], padx=8, pady=4, cursor="hand2"
            )
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, o=opt: self.select(o))
            self.buttons.append(btn)
    
    def select(self, option):
        self.current = option
        for btn, opt in zip(self.buttons, self.options):
            if opt == option:
                btn.config(fg="#ffffff", font=("Segoe UI", 12, "bold"))
            else:
                btn.config(fg="#6b7280", font=("Segoe UI", 12))
        self.callback(option)
    
    def update_bg(self, bg):
        self.configure(bg=bg)
        for btn in self.buttons:
            btn.configure(bg=bg)


# ============== CAT CLIENT UI ==============
class CatClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cat Client 1.0")
        self.root.geometry("900x560")
        self.root.resizable(False, False)
        
        self.theme_mode = "system"
        self.current_theme = THEMES[get_system_theme()]
        
        self.username = tk.StringVar(value="Player")
        self.version = tk.StringVar(value="1.20.1")
        self.account_type = tk.StringVar(value="Cat Client")
        self.ram = tk.IntVar(value=4)
        self.skin_photo = None
        self.status_text = tk.StringVar(value="Ready to play 🐱")
        self.java_bin = find_java()
        self.game_process = None
        self._log_handle = None
        
        GAME_DIR.mkdir(parents=True, exist_ok=True)
        
        self.setup_styles()
        self.build_ui()
        self.apply_theme()
        self.load_versions()
        
        self.root.after(500, self.update_skin)

    def ui_call(self, fn, *args, **kwargs):
        """Schedule a UI update on the main thread with captured arguments."""
        self.root.after(0, lambda f=fn, a=args, kw=kwargs: f(*a, **kw))
    
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
    
    def apply_theme(self):
        t = self.current_theme
        self.root.configure(bg=t["bg_dark"])
        
        self.style.configure("Cat.TCombobox",
            fieldbackground=t["bg_input"],
            background=t["bg_input"],
            foreground=t["text_primary"],
            arrowcolor=t["text_primary"],
            borderwidth=0
        )
        self.style.map("Cat.TCombobox",
            fieldbackground=[("readonly", t["bg_input"])],
            selectbackground=[("readonly", t["accent"])],
            selectforeground=[("readonly", t["text_primary"])]
        )
        
        self.style.configure("Cat.Horizontal.TProgressbar",
            troughcolor=t["bg_darker"],
            background=t["accent_green"],
            thickness=6
        )
        
        if hasattr(self, 'header'):
            self.header.configure(bg=t["bg_header"])
            for child in self.header.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=t["bg_header"])
                elif isinstance(child, tk.Frame):
                    child.configure(bg=t["bg_header"])
                    for c in child.winfo_children():
                        if isinstance(c, (tk.Label, tk.Frame)):
                            c.configure(bg=t["bg_header"])
        
        if hasattr(self, 'nav_bar'):
            self.nav_bar.configure(bg=t["bg_darker"])
            for child in self.nav_bar.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=t["bg_darker"])
        
        if hasattr(self, 'main_content'):
            self.update_frame_theme(self.main_content, t)
        
        if hasattr(self, 'bottom_bar'):
            self.bottom_bar.configure(bg=t["bg_darker"])
            self.update_frame_theme(self.bottom_bar, t, is_bottom=True)
        
        if hasattr(self, 'theme_toggle'):
            self.theme_toggle.update_bg(t["bg_header"])
        
        if hasattr(self, 'play_button'):
            self.play_button.configure(
                bg=t["button_play"],
                fg=t["button_play_text"],
                activebackground=t["button_play_hover"],
                activeforeground=t["button_play_text"],
            )
    
    def update_frame_theme(self, frame, t, is_bottom=False):
        bg = t["bg_darker"] if is_bottom else t["bg_dark"]
        try:
            frame.configure(bg=bg)
        except:
            pass
        
        for child in frame.winfo_children():
            try:
                widget_class = child.winfo_class()
                
                if widget_class == "Frame":
                    if child.cget("bg") in [THEMES["dark"]["bg_panel"], THEMES["light"]["bg_panel"], "#1f2937", "#ffffff"]:
                        child.configure(bg=t["bg_panel"])
                    elif child.cget("bg") in [THEMES["dark"]["bg_input"], THEMES["light"]["bg_input"], "#374151", "#f9fafb"]:
                        child.configure(bg=t["bg_input"])
                    else:
                        child.configure(bg=bg)
                    self.update_frame_theme(child, t, is_bottom)
                    
                elif widget_class == "Label":
                    parent_bg = child.master.cget("bg") if hasattr(child.master, 'cget') else bg
                    child.configure(bg=parent_bg)
                    
                    current_fg = child.cget("fg")
                    if current_fg in ["#ffffff", "#111827", t["text_primary"]]:
                        child.configure(fg=t["text_primary"])
                    elif current_fg in ["#9ca3af", "#4b5563", t["text_secondary"]]:
                        child.configure(fg=t["text_secondary"])
                    elif current_fg in ["#6b7280", t["text_muted"]]:
                        child.configure(fg=t["text_muted"])
                    elif current_fg in ["#10b981", "#059669", t["accent_green"]]:
                        child.configure(fg=t["accent_green"])
                    elif current_fg in ["#f59e0b", "#d97706", t["accent_orange"]]:
                        child.configure(fg=t["accent_orange"])
                
                elif widget_class == "Entry":
                    child.configure(
                        bg=t["bg_input"],
                        fg=t["text_primary"],
                        insertbackground=t["text_primary"]
                    )
                
                elif widget_class == "Button":
                    if "PLAY" in child.cget("text"):
                        child.configure(
                            bg=t["button_play"],
                            fg=t["button_play_text"],
                            activebackground=t["button_play_hover"],
                            activeforeground=t["button_play_text"],
                        )
                    else:
                        child.configure(
                            bg=t["bg_panel"],
                            fg=t["text_secondary"],
                            activebackground=t["bg_input"]
                        )
                
                elif widget_class == "Scale":
                    child.configure(
                        bg=bg,
                        fg=t["text_primary"],
                        troughcolor=t["bg_input"],
                        activebackground=t["accent_green"],
                        highlightbackground=bg
                    )
                
                elif widget_class == "Checkbutton":
                    child.configure(
                        bg=bg,
                        fg=t["text_secondary"],
                        activebackground=bg,
                        selectcolor=t["bg_input"]
                    )
            except:
                pass
    
    def on_theme_change(self, mode):
        self.theme_mode = mode
        if mode == "system":
            theme_name = get_system_theme()
        else:
            theme_name = mode
        self.current_theme = THEMES[theme_name]
        self.apply_theme()
    
    def build_ui(self):
        t = self.current_theme
        
        self.header = tk.Frame(self.root, bg=t["bg_header"], height=50)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        
        logo_frame = tk.Frame(self.header, bg=t["bg_header"])
        logo_frame.pack(side="left", padx=15)
        
        tk.Label(
            logo_frame, text="🐱 Cat Client", font=("Segoe UI", 14, "bold"),
            fg="#ffffff", bg=t["bg_header"]
        ).pack(side="left")
        
        tk.Label(
            logo_frame, text="1.0", font=("Segoe UI", 9),
            fg="#e0e0ff", bg=t["bg_header"]
        ).pack(side="left", padx=(8, 0))
        
        header_right = tk.Frame(self.header, bg=t["bg_header"])
        header_right.pack(side="right", padx=10)
        
        self.theme_toggle = ThemeToggle(
            header_right, self.on_theme_change, 
            initial="system", bg=t["bg_header"]
        )
        self.theme_toggle.pack(side="left", padx=(0, 20))
        
        for icon in ["─", "□", "✕"]:
            btn = tk.Label(
                header_right, text=icon, font=("Segoe UI", 12),
                fg="#ffffff", bg=t["bg_header"],
                padx=10, cursor="hand2"
            )
            btn.pack(side="left")
            if icon == "✕":
                btn.bind("<Button-1>", lambda e: self.root.quit())
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#e81123"))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=t["bg_header"]))
    
        self.nav_bar = tk.Frame(self.root, bg=t["bg_darker"], height=40)
        self.nav_bar.pack(fill="x")
        self.nav_bar.pack_propagate(False)
        
        tabs = ["PLAY", "MODS", "SKINS", "SETTINGS", "ABOUT"]
        self.tab_labels = []
        
        for i, tab in enumerate(tabs):
            lbl = tk.Label(
                self.nav_bar, text=tab, font=("Segoe UI", 10),
                fg=t["text_secondary"] if i > 0 else t["text_primary"],
                bg=t["bg_darker"], padx=20, pady=10, cursor="hand2"
            )
            lbl.pack(side="left")
            self.tab_labels.append(lbl)
            
            if i == 0:
                indicator = tk.Frame(lbl, bg=t["accent"], height=3)
                indicator.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")
        
        self.main_content = tk.Frame(self.root, bg=t["bg_dark"])
        self.main_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        left_panel = tk.Frame(self.main_content, bg=t["bg_dark"], width=200)
        left_panel.pack(side="left", fill="y", padx=(0, 20))
        left_panel.pack_propagate(False)
        
        skin_frame = tk.Frame(left_panel, bg=t["bg_panel"], width=180, height=200)
        skin_frame.pack(pady=(0, 15))
        skin_frame.pack_propagate(False)
        
        self.skin_label = tk.Label(
            skin_frame, text="🐱", font=("Segoe UI", 48),
            fg=t["text_secondary"], bg=t["bg_panel"]
        )
        self.skin_label.place(relx=0.5, rely=0.5, anchor="center")
        
        self.username_display = tk.Label(
            left_panel, textvariable=self.username, font=("Segoe UI", 11, "bold"),
            fg=t["text_primary"], bg=t["bg_dark"]
        )
        self.username_display.pack()
        
        self.account_indicator = tk.Label(
            left_panel, text="Cat Client Account", font=("Segoe UI", 9),
            fg=t["accent_green"], bg=t["bg_dark"]
        )
        self.account_indicator.pack(pady=(2, 15))
        
        manage_btn = tk.Button(
            left_panel, text="Manage accounts", font=("Segoe UI", 9),
            fg=t["text_secondary"], bg=t["bg_panel"],
            activeforeground=t["text_primary"],
            activebackground=t["bg_input"],
            relief="flat", cursor="hand2", padx=15, pady=5
        )
        manage_btn.pack()
        
        right_panel = tk.Frame(self.main_content, bg=t["bg_dark"])
        right_panel.pack(side="right", fill="both", expand=True)
        
        account_frame = tk.Frame(right_panel, bg=t["bg_dark"])
        account_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            account_frame, text="Account type:", font=("Segoe UI", 10),
            fg=t["text_secondary"], bg=t["bg_dark"]
        ).pack(side="left", padx=(0, 10))
        
        account_types = ["Cat Client", "Microsoft Account", "Mojang Account (Legacy)"]
        self.account_combo = ttk.Combobox(
            account_frame, textvariable=self.account_type,
            values=account_types, state="readonly", width=25,
            style="Cat.TCombobox", font=("Segoe UI", 10)
        )
        self.account_combo.pack(side="left")
        self.account_combo.bind("<<ComboboxSelected>>", self.on_account_type_change)
        
        self.cracked_label = tk.Label(
            account_frame, text="✓ OFFLINE MODE", font=("Segoe UI", 9, "bold"),
            fg=t["accent_green"], bg=t["bg_dark"]
        )
        self.cracked_label.pack(side="left", padx=(15, 0))
        
        username_frame = tk.Frame(right_panel, bg=t["bg_dark"])
        username_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            username_frame, text="Username:", font=("Segoe UI", 10),
            fg=t["text_secondary"], bg=t["bg_dark"]
        ).pack(side="left", padx=(0, 10))
        
        self.username_entry = tk.Entry(
            username_frame, textvariable=self.username, font=("Segoe UI", 11),
            fg=t["text_primary"], bg=t["bg_input"],
            insertbackground=t["text_primary"],
            relief="flat", width=30
        )
        self.username_entry.pack(side="left", ipady=8, padx=2)
        self.username_entry.bind("<KeyRelease>", self.on_username_change)
        
        version_frame = tk.Frame(right_panel, bg=t["bg_dark"])
        version_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            version_frame, text="Version:", font=("Segoe UI", 10),
            fg=t["text_secondary"], bg=t["bg_dark"]
        ).pack(side="left", padx=(0, 10))
        
        version_container = tk.Frame(version_frame, bg=t["bg_input"])
        version_container.pack(side="left")
        
        self.version_combo = ttk.Combobox(
            version_container, textvariable=self.version,
            state="readonly", width=35, style="Cat.TCombobox",
            font=("Segoe UI", 10)
        )
        self.version_combo.pack(side="left", ipady=6)
        
        refresh_btn = tk.Label(
            version_container, text="↻", font=("Segoe UI", 14),
            fg=t["text_secondary"], bg=t["bg_input"],
            padx=10, cursor="hand2"
        )
        refresh_btn.pack(side="left")
        refresh_btn.bind("<Button-1>", lambda e: self.load_versions())
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.config(fg=t["text_primary"]))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.config(fg=t["text_secondary"]))
        
        ram_frame = tk.Frame(right_panel, bg=t["bg_dark"])
        ram_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            ram_frame, text="RAM:", font=("Segoe UI", 10),
            fg=t["text_secondary"], bg=t["bg_dark"]
        ).pack(side="left", padx=(0, 10))
        
        self.ram_display = tk.Label(
            ram_frame, text="4096 MB", font=("Segoe UI", 10, "bold"),
            fg=t["accent_green"], bg=t["bg_dark"], width=10
        )
        self.ram_display.pack(side="left")
        
        ram_slider = tk.Scale(
            ram_frame, variable=self.ram, from_=1, to=16,
            orient="horizontal", length=300,
            bg=t["bg_dark"], fg=t["text_primary"],
            highlightthickness=0, troughcolor=t["bg_input"],
            activebackground=t["accent_green"],
            sliderrelief="flat", sliderlength=20, width=12,
            showvalue=False, command=self.on_ram_change
        )
        ram_slider.pack(side="left", padx=(10, 0))
        
        options_frame = tk.Frame(right_panel, bg=t["bg_dark"])
        options_frame.pack(fill="x", pady=(10, 20))
        
        self.fullscreen_var = tk.BooleanVar(value=False)
        self.download_assets_var = tk.BooleanVar(value=True)
        
        for text, var in [("Fullscreen", self.fullscreen_var), ("Download All Assets", self.download_assets_var)]:
            cb_frame = tk.Frame(options_frame, bg=t["bg_dark"])
            cb_frame.pack(side="left", padx=(0, 25))
            
            cb = tk.Checkbutton(
                cb_frame, text=text, variable=var,
                font=("Segoe UI", 10), fg=t["text_secondary"],
                bg=t["bg_dark"], activebackground=t["bg_dark"],
                activeforeground=t["text_primary"],
                selectcolor=t["bg_input"], cursor="hand2"
            )
            cb.pack()
        
        self.bottom_bar = tk.Frame(self.root, bg=t["bg_darker"], height=80)
        self.bottom_bar.pack(side="bottom", fill="x")
        self.bottom_bar.pack_propagate(False)
        
        status_frame = tk.Frame(self.bottom_bar, bg=t["bg_darker"])
        status_frame.pack(side="left", padx=20, pady=10)
        
        self.status_label = tk.Label(
            status_frame, textvariable=self.status_text, font=("Segoe UI", 9),
            fg=t["text_secondary"], bg=t["bg_darker"]
        )
        self.status_label.pack(anchor="w")
        
        self.progress_bar = ttk.Progressbar(
            status_frame, mode="determinate", length=400,
            style="Cat.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(anchor="w", pady=(5, 0))
        
        play_container = tk.Frame(self.bottom_bar, bg=t["bg_darker"])
        play_container.pack(side="right", padx=20, pady=15)
        
        self.play_button = tk.Button(
            play_container, text="🐱  PLAY MINECRAFT", font=("Segoe UI", 14, "bold"),
            fg=t["button_play_text"], bg=t["button_play"],
            activeforeground=t["button_play_text"],
            activebackground=t["button_play_hover"],
            relief="flat", cursor="hand2", padx=40, pady=12,
            command=self.play
        )
        self.play_button.pack()
        
        self.play_button.bind("<Enter>", lambda e: self.play_button.config(bg=self.current_theme["button_play_hover"]))
        self.play_button.bind("<Leave>", lambda e: self.play_button.config(bg=self.current_theme["button_play"]))
    
    # ============== EVENT HANDLERS ==============
    def on_account_type_change(self, event=None):
        t = self.current_theme
        acc_type = self.account_type.get()
        
        if acc_type == "Cat Client":
            self.cracked_label.config(text="✓ OFFLINE MODE", fg=t["accent_green"])
            self.account_indicator.config(text="Cat Client Account", fg=t["accent_green"])
            self.username_entry.config(state="normal")
        elif acc_type == "Microsoft Account":
            self.cracked_label.config(text="⚠ REQUIRES LOGIN", fg=t["accent_orange"])
            self.account_indicator.config(text="Not Logged In", fg=t["accent_orange"])
            messagebox.showinfo("Cat Client", 
                "Microsoft authentication is not available.\n\n"
                "Use 'Cat Client' mode for offline play! 🐱")
            self.account_type.set("Cat Client")
            self.on_account_type_change()
        else:
            self.cracked_label.config(text="⚠ DEPRECATED", fg=t["accent_orange"])
            messagebox.showinfo("Cat Client", 
                "Mojang accounts have been migrated to Microsoft.\n\n"
                "Use 'Cat Client' mode for offline play! 🐱")
            self.account_type.set("Cat Client")
            self.on_account_type_change()
    
    def on_username_change(self, event=None):
        if hasattr(self, '_skin_timer'):
            self.root.after_cancel(self._skin_timer)
        self._skin_timer = self.root.after(600, self.update_skin)
    
    def on_ram_change(self, value):
        mb = int(float(value)) * 1024
        self.ram_display.config(text=f"{mb} MB")
    
    def update_skin(self):
        username = self.username.get().strip()
        if not username:
            self.skin_label.config(text="🐱", image="", font=("Segoe UI", 48))
            return
        
        def load():
            short = username[:8]
            try:
                url = f"{SKIN_SERVER}/head/{username}/150.png"
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                    data = resp.read()
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(io.BytesIO(data))
                    photo = ImageTk.PhotoImage(img)
                    self.root.after(0, lambda p=photo: self._apply_skin_photo(p))
                except ImportError:
                    self.root.after(0, lambda t=f"🐱\n{short}": self._apply_skin_fallback(t))
            except Exception:
                self.root.after(0, lambda t=f"🐱\n{short}": self._apply_skin_fallback(t))
        
        threading.Thread(target=load, daemon=True).start()

    def _apply_skin_photo(self, photo):
        self.skin_photo = photo
        self.skin_label.config(image=self.skin_photo, text="")

    def _apply_skin_fallback(self, text):
        self.skin_label.config(image="", text=text, font=("Segoe UI", 24))
    
    def load_versions(self):
        self.status_text.set("Loading versions... 🐱")
        
        def load():
            try:
                data = fetch_version_manifest(timeout=10)
                versions = []
                for v in data["versions"]:
                    if v["type"] == "release":
                        versions.append(f"{v['id']} (release)")
                    elif v["type"] == "snapshot" and len(versions) < 60:
                        versions.append(f"{v['id']} (snapshot)")
                    if len(versions) >= 80:
                        break
                self.root.after(0, lambda v=versions: self.set_versions(v))
            except Exception:
                fallback = ["1.21.4 (release)", "1.20.1 (release)", "1.19.4 (release)", "1.18.2 (release)"]
                self.root.after(0, lambda v=fallback: self.set_versions(v))
        
        threading.Thread(target=load, daemon=True).start()
    
    def set_versions(self, versions):
        self.version_combo["values"] = versions
        if versions:
            self.version.set(versions[0])
        self.status_text.set("Ready to play 🐱")
    
    # ============== DOWNLOAD & LAUNCH ==============
    def download_file(self, url, dest_path, expected_hash=None, expected_size=None):
        return download_file_fast(url, dest_path, expected_hash, expected_size, timeout=60)

    def _download_lib_task(self, task):
        url, dest_path, sha1, size = task
        return download_file_fast(url, dest_path, sha1, size, timeout=60)

    def extract_natives(self, native_path, natives_dir):
        try:
            with zipfile.ZipFile(native_path, 'r') as z:
                for f in z.namelist():
                    if f.startswith("META-INF/"):
                        continue
                    if f.endswith(('.so', '.dll', '.dylib', '.jnilib')):
                        target = natives_dir / Path(f).name
                        with z.open(f) as src, open(target, 'wb') as dst:
                            dst.write(src.read())
                        if sys.platform != "win32":
                            os.chmod(target, 0o755)
        except (zipfile.BadZipFile, OSError) as e:
            print(f"Native extract failed: {e}")
    
    def download_version(self, version_id, progress_cb=None, status_cb=None):
        actual_id = version_id.split(" (")[0] if " (" in version_id else version_id
        
        if status_cb:
            status_cb(f"Fetching {actual_id}... 🐱")
        
        manifest = fetch_version_manifest(timeout=15)
        
        version_url = None
        for v in manifest["versions"]:
            if v["id"] == actual_id:
                version_url = v["url"]
                break
        
        if not version_url:
            raise ValueError(f"Version {actual_id} not found")
        
        version_info = fetch_json(version_url, timeout=15)
        
        version_dir = GAME_DIR / "versions" / actual_id
        version_dir.mkdir(parents=True, exist_ok=True)
        natives_dir = version_dir / "natives"
        natives_dir.mkdir(parents=True, exist_ok=True)
        libs_dir = GAME_DIR / "libraries"
        libs_dir.mkdir(parents=True, exist_ok=True)
        
        version_json_path = version_dir / f"{actual_id}.json"
        with open(version_json_path, 'w') as f:
            json.dump(version_info, f, indent=2)
        
        jar_path = version_dir / f"{actual_id}.jar"
        client = version_info["downloads"]["client"]
        client_url = client["url"]
        client_sha1 = client.get("sha1")
        client_size = client.get("size")
        if not file_is_valid(jar_path, client_sha1, client_size):
            if status_cb:
                status_cb(f"Downloading {actual_id}.jar... 🐱")
            if not self.download_file(client_url, jar_path, client_sha1, client_size):
                raise RuntimeError(f"Failed to download {actual_id}.jar")
        
        libraries = version_info.get("libraries", [])
        os_name = get_os_name()
        download_tasks = []
        native_paths = []
        
        for lib in libraries:
            if "rules" in lib and not check_rules(lib["rules"]):
                continue
            
            if "downloads" not in lib:
                continue
            
            if "artifact" in lib["downloads"]:
                artifact = lib["downloads"]["artifact"]
                lib_path = libs_dir / artifact["path"]
                if not file_is_valid(lib_path, artifact.get("sha1"), artifact.get("size")):
                    download_tasks.append((
                        artifact["url"],
                        lib_path,
                        artifact.get("sha1"),
                        artifact.get("size"),
                    ))
            
            if "natives" in lib:
                native_key = lib["natives"].get(os_name, "")
                if "${arch}" in native_key:
                    bits = "64" if get_arch() in ("x64", "arm64") else "32"
                    native_key = native_key.replace("${arch}", bits)
                
                if native_key and "classifiers" in lib["downloads"]:
                    native_info = lib["downloads"]["classifiers"].get(native_key)
                    if native_info:
                        native_path = libs_dir / native_info["path"]
                        if not file_is_valid(native_path, native_info.get("sha1"), native_info.get("size")):
                            download_tasks.append((
                                native_info["url"],
                                native_path,
                                native_info.get("sha1"),
                                native_info.get("size"),
                            ))
                        native_paths.append(native_path)
        
        if download_tasks:
            if status_cb:
                status_cb(f"Downloading {len(download_tasks)} libraries... 🐱")
            with concurrent.futures.ThreadPoolExecutor(max_workers=LIB_WORKERS) as executor:
                results = list(executor.map(self._download_lib_task, download_tasks))
            if not all(results):
                raise RuntimeError("Some libraries failed to download")
        
        for native_path in native_paths:
            if native_path.exists():
                self.extract_natives(native_path, natives_dir)
        
        if self.download_assets_var.get():
            asset_index = version_info["assetIndex"]
            asset_index_id = asset_index["id"]
            asset_index_url = asset_index["url"]
            
            if status_cb:
                status_cb(f"Downloading assets... 🐱")
            
            asset_downloader = AssetDownloader(
                GAME_DIR,
                progress_callback=progress_cb,
                status_callback=status_cb
            )
            
            asset_downloader.download_all_assets(asset_index_id, asset_index_url)
        else:
            asset_index = version_info["assetIndex"]
            index_path = GAME_DIR / "assets" / "indexes" / f"{asset_index['id']}.json"
            if not index_path.exists():
                self.download_file(asset_index["url"], index_path, asset_index.get("sha1"))
        
        if status_cb:
            status_cb(f"{actual_id} ready! 🐱")
        
        return version_info, actual_id

    def build_launch_args(self, version_info, actual_id, username, ram_mb, natives_dir, classpath):
        main_class = version_info.get("mainClass", "net.minecraft.client.main.Main")
        offline_uuid = generate_offline_uuid(username)
        variables = {
            "natives_directory": str(natives_dir.resolve()),
            "launcher_name": "CatClient",
            "launcher_version": "1.0",
            "classpath": classpath,
            "auth_player_name": username,
            "version_name": actual_id,
            "game_directory": str(GAME_DIR.resolve()),
            "assets_root": str((GAME_DIR / "assets").resolve()),
            "assets_index_name": version_info["assetIndex"]["id"],
            "auth_uuid": offline_uuid,
            "auth_access_token": "0",
            "clientid": "",
            "auth_xuid": "",
            "user_type": "legacy",
            "version_type": version_info.get("type", "release"),
        }
        features = {
            "is_demo_user": False,
            "has_custom_resolution": False,
            "has_quick_plays_support": False,
            "is_quick_play_singleplayer": False,
            "is_quick_play_multiplayer": False,
            "is_quick_play_realms": False,
        }
        memory = [self.java_bin, f"-Xmx{ram_mb}M", "-Xms512M"]

        if "arguments" in version_info:
            jvm_args = expand_arguments(version_info["arguments"].get("jvm", []), variables, features)
            game_args = expand_arguments(version_info["arguments"].get("game", []), variables, features)
            args = memory + jvm_args + [main_class] + game_args
        else:
            args = memory + [
                f"-Djava.library.path={natives_dir.resolve()}",
                "-Dminecraft.launcher.brand=CatClient",
                "-Dminecraft.launcher.version=1.0",
                "-cp", classpath,
                main_class,
                "--username", username,
                "--version", actual_id,
                "--gameDir", str(GAME_DIR.resolve()),
                "--assetsDir", str((GAME_DIR / "assets").resolve()),
                "--assetIndex", version_info["assetIndex"]["id"],
                "--uuid", offline_uuid,
                "--accessToken", "0",
                "--userType", "legacy",
                "--versionType", version_info.get("type", "release"),
            ]

        if self.fullscreen_var.get() and "--fullscreen" not in args:
            args.append("--fullscreen")
        return args

    def _monitor_game(self, process, actual_id, log_handle):
        try:
            exit_code = process.wait()
            if exit_code == 0:
                status = "Game closed"
            else:
                status = f"Game exited (code {exit_code}) — see logs/catclient-latest.log"
            self.ui_call(self.status_text.set, status)
        except Exception:
            self.ui_call(self.status_text.set, "Game monitor stopped")
        finally:
            if log_handle:
                try:
                    log_handle.close()
                except Exception:
                    pass
            self._log_handle = None
            self.game_process = None
            self.ui_call(self.play_button.config, state="normal", text="🐱  PLAY MINECRAFT")
    
    def play(self):
        username = self.username.get().strip()
        if not username:
            messagebox.showwarning("Cat Client", "Enter a username! 🐱")
            return
        
        if not all(c.isalnum() or c == "_" for c in username):
            messagebox.showwarning("Cat Client", "Invalid username! Use only letters, numbers, underscore. 🐱")
            return
        
        if len(username) < 3 or len(username) > 16:
            messagebox.showwarning("Cat Client", "Username must be 3-16 characters! 🐱")
            return
        
        version = self.version.get()
        if not version:
            messagebox.showwarning("Cat Client", "Select a version! 🐱")
            return
        
        if self.account_type.get() != "Cat Client":
            messagebox.showwarning("Cat Client", "Only Cat Client (offline) mode is available. 🐱")
            self.account_type.set("Cat Client")
            return

        if self.game_process and self.game_process.poll() is None:
            messagebox.showinfo("Cat Client", "Minecraft is already running.")
            return
        
        self.play_button.config(state="disabled", text="LAUNCHING... 🐱")
        self.progress_bar.config(value=0)
        
        def launch():
            try:
                version_info, actual_id = self.download_version(
                    version,
                    progress_cb=lambda p: self.ui_call(self.progress_bar.config, value=p),
                    status_cb=lambda s: self.ui_call(self.status_text.set, s)
                )
                
                version_dir = GAME_DIR / "versions" / actual_id
                jar_path = version_dir / f"{actual_id}.jar"
                if not jar_path.exists():
                    raise FileNotFoundError(f"Missing game jar: {jar_path}")
                natives_dir = version_dir / "natives"
                libs_dir = GAME_DIR / "libraries"
                
                classpath_parts = []
                for lib in version_info.get("libraries", []):
                    if "rules" in lib and not check_rules(lib["rules"]):
                        continue
                    if "downloads" in lib and "artifact" in lib["downloads"]:
                        lib_path = libs_dir / lib["downloads"]["artifact"]["path"]
                        if lib_path.exists():
                            classpath_parts.append(str(lib_path))
                
                classpath_parts.append(str(jar_path))
                classpath = CLASSPATH_SEP.join(classpath_parts)
                ram_mb = self.ram.get() * 1024
                args = self.build_launch_args(
                    version_info, actual_id, username, ram_mb, natives_dir, classpath
                )
                
                self.ui_call(self.status_text.set, f"Launching {actual_id}...")
                
                log_dir = GAME_DIR / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                log_path = log_dir / "catclient-latest.log"
                log_handle = open(log_path, "w", encoding="utf-8")
                self._log_handle = log_handle
                
                process = subprocess.Popen(
                    args,
                    cwd=str(GAME_DIR),
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                )
                self.game_process = process
                self.ui_call(self.status_text.set, f"Playing {actual_id}")
                
                threading.Thread(
                    target=self._monitor_game,
                    args=(process, actual_id, log_handle),
                    daemon=True,
                ).start()
                
            except Exception as e:
                import traceback
                err = str(e)
                self.ui_call(self.status_text.set, "Launch failed!")
                self.ui_call(messagebox.showerror, "Cat Client", f"Error:\n{err}")
                print(traceback.format_exc())
                if self._log_handle:
                    try:
                        self._log_handle.close()
                    except Exception:
                        pass
                    self._log_handle = None
                self.game_process = None
                self.ui_call(self.play_button.config, state="normal", text="🐱  PLAY MINECRAFT")
        
        threading.Thread(target=launch, daemon=True).start()


# ============== MAIN ==============
if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
    try:
        from PIL import Image, ImageTk
    except ImportError:
        print("Install Pillow for skin previews: pip install pillow")
    
    root = tk.Tk()
    app = CatClientApp(root)
    root.mainloop()
