#!/usr/bin/env python3
"""rb ghostbuster - Duplicate Track Remover for rekordbox 6/7.

Finds duplicate tracks in a rekordbox library and removes them.
Playlist, tag and history entries of a removed copy are moved to the copy
that stays. Cue points of a removed copy are deleted - the kept copy keeps
its own cues, which is why the copy with the most cues is recommended.

rb ghostbuster never works on your original library directly.
It works on a copy inside its own folder, and only writes the result
back to rekordbox when you confirm it.

Credits:
- Inspired by pyrekordbox (https://github.com/dylanljones/pyrekordbox)
- Database access via sqlcipher3 (https://pypi.org/project/sqlcipher3-wheels/)
- Everything else is Python standard library

Version: 0.2.0
Author: djoshi
"""

import os
import sys


# =====================================================================
#  Console window (so double-clicking the .pyw file shows a window)
# =====================================================================
def ensure_console():
    """Open a console window when started with pythonw (.pyw file)."""
    if os.name != "nt":
        return
    if sys.stdout is not None and sys.stdin is not None:
        return
    try:
        import ctypes

        ctypes.windll.kernel32.AllocConsole()
        sys.stdout = open("CONOUT$", "w", buffering=1, encoding="utf-8",
                          errors="replace")
        sys.stderr = open("CONOUT$", "w", buffering=1, encoding="utf-8",
                          errors="replace")
        sys.stdin = open("CONIN$", "r", encoding="utf-8", errors="replace")
        ctypes.windll.kernel32.SetConsoleTitleW("rb ghostbuster")
    except Exception:
        pass


ensure_console()


# =====================================================================
#  Auto-install the one library rb ghostbuster needs
# =====================================================================
def pip_python():
    """Return a python executable that can run pip (not pythonw)."""
    exe = sys.executable or "python"
    if exe.lower().endswith("pythonw.exe"):
        candidate = exe[: -len("pythonw.exe")] + "python.exe"
        if os.path.exists(candidate):
            return candidate
    return exe


def private_venv_dir():
    """A private Python environment inside the rb ghostbuster folder."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")


def venv_site_packages():
    """site-packages of the private environment, if it exists."""
    venv = private_venv_dir()
    if os.name == "nt":
        path = os.path.join(venv, "Lib", "site-packages")
        return path if os.path.isdir(path) else None
    lib = os.path.join(venv, "lib")
    if os.path.isdir(lib):
        for name in sorted(os.listdir(lib)):
            path = os.path.join(lib, name, "site-packages")
            if os.path.isdir(path):
                return path
    return None


def venv_python():
    venv = private_venv_dir()
    if os.name == "nt":
        return os.path.join(venv, "Scripts", "python.exe")
    return os.path.join(venv, "bin", "python")


def add_import_paths():
    """Make installed packages findable (private environment and user site)."""
    import site as site_module
    import importlib

    paths = []
    venv_site = venv_site_packages()
    if venv_site:
        paths.append(venv_site)
    try:
        paths.append(site_module.getusersitepackages())
    except Exception:
        pass

    for path in paths:
        if path and path not in sys.path:
            sys.path.insert(0, path)
    importlib.invalidate_caches()


def import_sqlcipher():
    """True when the sqlcipher3 package can be imported."""
    import importlib

    importlib.invalidate_caches()
    try:
        import sqlcipher3  # noqa: F401
        return True
    except ImportError:
        return False


def pip_install(package, flags):
    """Run pip quietly. Returns (ok, last_output)."""
    import subprocess

    cmd = [pip_python(), "-m", "pip", "install", "--quiet"] + list(flags) + [package]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as exc:
        return False, str(exc)
    output = (result.stderr or result.stdout or "").strip()
    return result.returncode == 0, output


def install_in_private_venv():
    """Last resort: install into a venv inside this folder."""
    import subprocess

    venv = private_venv_dir()
    try:
        subprocess.run([pip_python(), "-m", "venv", venv],
                       capture_output=True, text=True)
    except Exception as exc:
        return False, f"could not create .venv ({exc})"
    if not os.path.exists(venv_python()):
        return False, "could not create .venv (python3-venv may be missing)"

    try:
        result = subprocess.run(
            [venv_python(), "-m", "pip", "install", "--quiet",
             "sqlcipher3-wheels"],
            capture_output=True, text=True)
    except Exception as exc:
        return False, str(exc)
    output = (result.stderr or result.stdout or "").strip()
    return result.returncode == 0, output


def ensure_dependencies():
    """Install sqlcipher3 on first start, so double-clicking just works.

    Tries the normal user install first. On Linux and Homebrew macOS, pip
    refuses with "externally-managed-environment"; there we retry with the
    user-only override flag, and finally fall back to a private .venv folder
    next to this script. Nothing is ever installed system-wide.
    """
    add_import_paths()
    if import_sqlcipher():
        return

    print("First start: installing one small helper library")
    print("(this happens only once, please wait)...")
    print()

    installed = False
    last_error = ""
    for package in ("sqlcipher3-wheels", "sqlcipher3-binary"):
        for flags in (("--user",), ("--user", "--break-system-packages")):
            ok, output = pip_install(package, flags)
            if ok:
                add_import_paths()
                if import_sqlcipher():
                    installed = True
                    break
            elif output:
                last_error = output
        if installed:
            break

    if not installed:
        print("Normal install was blocked, trying a private environment")
        print("inside the rb ghostbuster folder (nothing system-wide)...")
        ok, output = install_in_private_venv()
        if output:
            last_error = output
        if ok:
            add_import_paths()
            installed = import_sqlcipher()

    if installed:
        print("Done. Starting rb ghostbuster...")
        print()
        return

    print()
    print("Could not install the database library automatically.")
    print("Please open Terminal, go to the rb ghostbuster folder and paste")
    print("this one line (it is a single command):")
    print()
    if os.name == "nt":
        print("  py -m pip install --user sqlcipher3-wheels")
    else:
        print(f'  "{pip_python()}" -m pip install --user '
              "--break-system-packages sqlcipher3-wheels")
    print()
    print("Then start rb ghostbuster again.")
    if last_error:
        print()
        print("Last message from pip:")
        print("  " + last_error.replace("\n", "\n  ")[:600])
    try:
        input("\nPress Enter to close this window...")
    except EOFError:
        pass
    sys.exit(1)


ensure_dependencies()


# =====================================================================
#  Imports
# =====================================================================
import csv
import ctypes
import glob
import json
import math
import re
import shutil
import subprocess
import unicodedata
from collections import defaultdict
from datetime import datetime
from itertools import combinations


# =====================================================================
#  Colors - Mango & Lime
# =====================================================================
MANGO = "\033[38;5;208m"
LIME = "\033[38;5;150m"     # soft sage green - easier on the eyes than neon lime
PURPLE = "\033[38;5;141m"
RESET = "\033[0m"


def enable_ansi():
    """Let the Windows console show the colors."""
    if os.name != "nt":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


enable_ansi()

_color_i = 0


def set_color(text, color):
    return f"{color}{text}{RESET}"


def say(text="", color=None):
    """Print a line, alternating mango and lime when no color is given."""
    global _color_i
    if color is None:
        color = LIME if _color_i % 2 == 0 else MANGO
        _color_i += 1
    print(set_color(text, color), flush=True)


def prompt(text):
    """Colored input prompt."""
    global _color_i
    color = LIME if _color_i % 2 == 0 else MANGO
    _color_i += 1
    try:
        return input(set_color(text, color)).strip()
    except EOFError:
        return ""


def press_enter(text="\nPress Enter to continue..."):
    prompt(text)


def yes(question):
    """Ask a yes/no question, accepting English and German answers."""
    while True:
        answer = prompt(f"{question} (y/n): ").lower()
        if answer in ("y", "yes", "j", "ja"):
            return True
        if answer in ("n", "no", "nein"):
            return False
        say("Please type y or n and press Enter.", MANGO)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# =====================================================================
#  Configuration
# =====================================================================
APP = "rb ghostbuster"
VERSION = "0.2.0"
DEFAULT_KEY = "402fd482c38817c35ffa8ffb8c7d93143b749e7d315df7a81732a1ff43608497"
LENGTH_TOLERANCE = 3   # seconds; a bigger difference is a different version
KEEP_BACKUPS = 10      # how many backups of each kind are kept


def script_dir():
    """Folder this program sits in. Everything it needs lives here."""
    return os.path.dirname(os.path.abspath(__file__))


def master_db_path():
    return os.path.join(script_dir(), "master.db")


def settings_path():
    return os.path.join(script_dir(), "settings.json")


def backups_dir():
    return os.path.join(script_dir(), "backups")


def decisions_path():
    return os.path.join(script_dir(), "decisions.json")


def log_csv_path():
    return os.path.join(script_dir(), "duplicates_log.csv")


def delete_list_path():
    return os.path.join(script_dir(), "files_to_delete.txt")


def quarantine_log_path():
    return os.path.join(script_dir(), "quarantine_log.csv")


def quarantine_dir():
    path = load_settings().get("quarantine_folder")
    if path:
        return path
    return os.path.join(script_dir(), "quarantine")


# =====================================================================
#  Settings
# =====================================================================
def load_settings():
    try:
        with open(settings_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_settings(data):
    with open(settings_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update_settings(**changes):
    settings = load_settings()
    settings.update(changes)
    save_settings(settings)


def current_key():
    return load_settings().get("sqlcipher_key") or DEFAULT_KEY


# =====================================================================
#  Small helpers
# =====================================================================
def line(char="-", width=60):
    print(set_color(char * width, MANGO), flush=True)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)


def same_path(a, b):
    """True when two paths point to the same file (case-insensitive on Windows)."""
    if not a or not b:
        return False
    return (os.path.normcase(os.path.abspath(a))
            == os.path.normcase(os.path.abspath(b)))


def clean_entered_path(text):
    """Remove quotes and the '&' PowerShell adds when a file is dragged in."""
    return text.strip().lstrip("&").strip().strip('"').strip("'")


def fmt_len(seconds):
    return f"{seconds // 60}:{seconds % 60:02d}" if seconds else "?:??"


def strip_accents(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def clean(s):
    s = strip_accents(s).lower()
    s = re.sub(r"[^\w\s]|_", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def title_keys(title):
    raw = str(title or "")
    full = clean(raw)
    core = re.sub(r"[\(\[\{].*?[\)\]\}]", " ", raw)
    core = re.split(r"\s[-–—]\s", core)[0]
    return full, (clean(core) or full)


ARTIST_SPLIT = re.compile(
    r"\s*(?:/|;|,|&|\+|\bfeat\b\.?|\bft\b\.?|\bfeaturing\b|\bvs\b\.?)\s*|\s+x\s+",
    re.I,
)


def artist_set(artist):
    s = strip_accents(artist).lower()
    return frozenset(p for p in (clean(x) for x in ARTIST_SPLIT.split(s)) if p)


def normpath(p):
    return os.path.normcase(os.path.normpath(p)) if p else ""


COPY_NAME = re.compile(r"(\(\d+\)|\bcopy\b|\bkopie\b)\s*$", re.I)


def score(track):
    """Which copy is the best one to keep (higher is better)."""
    stem = os.path.splitext(os.path.basename(track["path"]))[0]
    tid = int(track["id"]) if track["id"].isdigit() else 0
    return (track["exists"], track["cues"], bool(track["artists"]),
            len(track["pls"]), track["bitrate"], track["plays"], track["rating"],
            not COPY_NAME.search(stem),   # "song (1).mp3" / "song - Copy.mp3" lose
            -len(track["path"]),          # shorter path wins
            -tid)                         # imported first wins


# =====================================================================
#  SQLCipher
# =====================================================================
_sqlcipher = None


def load_sqlcipher():
    global _sqlcipher
    if _sqlcipher is not None:
        return _sqlcipher
    try:
        from sqlcipher3 import dbapi2
    except ImportError:
        import site
        import importlib

        user_site = site.getusersitepackages()
        if user_site and user_site not in sys.path:
            sys.path.append(user_site)
        importlib.invalidate_caches()
        from sqlcipher3 import dbapi2
    _sqlcipher = dbapi2
    return _sqlcipher


def open_db(path, key=None):
    """Open a rekordbox database. Raises if the key is wrong."""
    dbapi2 = load_sqlcipher()
    con = dbapi2.connect(path)
    safe_key = (key or current_key()).replace("'", "''")
    con.execute(f"PRAGMA key='{safe_key}'")
    # Touching the schema proves the key works.
    con.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
    return con


def check_db(path, key=None):
    """(True, track_count) or (False, reason)."""
    if not path or not os.path.isfile(path):
        return False, "file not found"
    con = None
    try:
        con = open_db(path, key)
        n = con.execute("SELECT COUNT(*) FROM djmdContent").fetchone()[0]
        return True, n
    except Exception as exc:
        return False, str(exc)
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:
                pass


# =====================================================================
#  rekordbox running?
# =====================================================================
def rekordbox_running():
    try:
        if os.name == "nt":
            out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"],
                                 capture_output=True, text=True,
                                 errors="ignore").stdout
        else:
            out = subprocess.run(["ps", "-A", "-o", "comm"],
                                 capture_output=True, text=True,
                                 errors="ignore").stdout
        return "rekordbox" in out.lower()
    except Exception:
        return False


def wait_for_rekordbox_closed():
    while rekordbox_running():
        say("")
        say("rekordbox is still running. Please close rekordbox AND")
        say("rekordboxAgent (small icon next to the clock: right-click > Quit).")
        prompt("Press Enter when both are closed... ")


# =====================================================================
#  Find the original rekordbox library
# =====================================================================
def find_db_path_in(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "db-path" and isinstance(v, str):
                return v
            found = find_db_path_in(v)
            if found:
                return found
    elif isinstance(obj, list):
        if len(obj) == 2 and obj[0] == "db-path" and isinstance(obj[1], str):
            return obj[1]
        for v in obj:
            found = find_db_path_in(v)
            if found:
                return found
    return None


def library_candidates():
    home = os.path.expanduser("~")
    appdata = os.environ.get("APPDATA", "")
    candidates = []

    for options_file in (
        os.path.join(appdata, "Pioneer", "rekordboxAgent", "storage", "options.json"),
        os.path.join(home, "Library", "Application Support", "Pioneer",
                     "rekordboxAgent", "storage", "options.json"),
    ):
        found = find_db_path_in(load_json(options_file, None))
        if found:
            candidates.append(found if found.endswith(".db")
                              else os.path.join(found, "master.db"))

    if appdata:
        candidates.append(os.path.join(appdata, "Pioneer", "rekordbox", "master.db"))
    if sys.platform == "darwin":
        candidates.append(os.path.join(home, "Library", "Pioneer", "rekordbox",
                                       "master.db"))
        candidates.append(os.path.join(home, "Library", "Application Support",
                                       "Pioneer", "rekordbox", "master.db"))
    candidates.append(os.path.join(home, ".local", "share", "Pioneer", "rekordbox",
                                   "master.db"))

    result, seen = [], set()
    for c in candidates:
        key = os.path.normcase(os.path.normpath(c))
        if key not in seen:
            seen.add(key)
            result.append(os.path.normpath(c))
    return result


def find_rekordbox_library():
    """First library that really opens; else the first one that exists."""
    candidates = library_candidates()
    for path in candidates:
        if check_db(path)[0]:
            return path
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


# =====================================================================
#  Copy + change detection
# =====================================================================
def fingerprint(path):
    """Size + modification time of master.db and its -wal file."""
    fp = []
    for suffix in ("", "-wal"):
        try:
            st = os.stat(path + suffix)
            fp += [st.st_size, int(st.st_mtime)]
        except OSError:
            fp += [0, 0]
    return fp


def original_changed(original, db):
    """True when rekordbox may have changed the original since the copy was made."""
    if not original or not os.path.isfile(original) or same_path(original, db):
        return False
    saved = load_settings().get("original_fingerprint")
    if not saved:
        return True          # unknown -> play it safe
    return fingerprint(original) != saved


def copy_library(source):
    """Copy master.db (and its -wal/-shm) into the project folder."""
    dest = master_db_path()
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    if not same_path(source, dest):
        shutil.copy2(source, dest)
        for suffix in ("-wal", "-shm"):
            if os.path.exists(source + suffix):
                shutil.copy2(source + suffix, dest + suffix)
            elif os.path.exists(dest + suffix):
                try:
                    os.remove(dest + suffix)
                except Exception:
                    pass

    settings = load_settings()
    if settings.get("pending_writeback"):
        # The old copy was never written back, so its leftover files
        # are still used by rekordbox - they must not be quarantined.
        settings["pending_quarantine"] = []
    settings["db"] = dest
    settings["original_library"] = source
    settings["original_fingerprint"] = fingerprint(source)
    settings["pending_writeback"] = False
    save_settings(settings)
    return dest


# =====================================================================
#  Backup / restore
# =====================================================================
def unique_folder(base):
    if not os.path.exists(base):
        return base
    n = 2
    while os.path.exists(f"{base}_{n}"):
        n += 1
    return f"{base}_{n}"


def make_backup(db, prefix=""):
    """Copy the library into backups/<day-month-year_time>/ and verify it."""
    os.makedirs(backups_dir(), exist_ok=True)
    stamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    dest = unique_folder(os.path.join(backups_dir(), prefix + stamp))
    os.makedirs(dest)

    try:
        for suffix in ("", "-wal", "-shm"):
            if os.path.exists(db + suffix):
                shutil.copy2(db + suffix, os.path.join(dest, "master.db" + suffix))

        with open(os.path.join(dest, "original_location.txt"), "w",
                  encoding="utf-8") as f:
            f.write(db)

        ok, info = check_db(os.path.join(dest, "master.db"))
        if not ok:
            raise RuntimeError(f"Backup could not be verified ({info}). "
                               "Stopping to be safe.")
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    prune_backups()
    return dest


def list_backups():
    folders = [f for f in glob.glob(os.path.join(backups_dir(), "*"))
               if os.path.isfile(os.path.join(f, "master.db"))]
    return sorted(folders, key=os.path.getmtime, reverse=True)


def prune_backups():
    """Keep only the newest KEEP_BACKUPS of each kind, so disk use stays bounded."""
    folders = list_backups()                 # newest first
    originals = [f for f in folders
                 if os.path.basename(f).startswith("original_before_replace_")]
    others = [f for f in folders if f not in originals]
    for folder in others[KEEP_BACKUPS:] + originals[KEEP_BACKUPS:]:
        shutil.rmtree(folder, ignore_errors=True)


def backup_source_label(folder, original):
    try:
        with open(os.path.join(folder, "original_location.txt"),
                  encoding="utf-8") as f:
            src = f.read().strip()
    except Exception:
        return "unknown source"
    if same_path(src, original):
        return "from rekordbox library"
    if same_path(src, master_db_path()):
        return "from working copy"
    return "from other file"


def checkpoint(db):
    """Fold the -wal journal into master.db, so it is one complete file."""
    con = open_db(db)
    try:
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        con.close()


def replace_db_file(target, source_db):
    """Overwrite target with source_db without ever leaving a half-written file."""
    checkpoint(source_db)
    tmp = target + ".rbg-tmp"
    shutil.copy2(source_db, tmp)
    ok, info = check_db(tmp)
    for suffix in ("-wal", "-shm"):          # checking may leave these behind
        if os.path.exists(tmp + suffix):
            os.remove(tmp + suffix)
    if not ok:
        os.remove(tmp)
        raise RuntimeError(f"temporary copy is unreadable ({info})")

    # Move the old journal aside (not delete), so a crash stays recoverable.
    aside = []
    for suffix in ("-wal", "-shm"):
        if os.path.exists(target + suffix):
            os.replace(target + suffix, target + suffix + ".rbg-old")
            aside.append(target + suffix + ".rbg-old")
    try:
        os.replace(tmp, target)              # atomic on the same drive
    except Exception:
        for path in aside:                   # put the old journal back
            try:
                os.replace(path, path[: -len(".rbg-old")])
            except OSError:
                pass
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    for path in aside:
        try:
            os.remove(path)
        except OSError:
            pass


def restore_backup(db, original):
    folders = list_backups()
    if not folders:
        say("No backups found yet.")
        return
    folders = folders[:15]

    # Where should the backup go?
    target = db
    if original and os.path.isfile(original) and not same_path(original, db):
        say("Restore into which library?")
        print(f"  {MANGO}[1]{RESET} {LIME}The working copy (rekordbox is not changed){RESET}")
        print(f"  {MANGO}[2]{RESET} {LIME}Your real rekordbox library "
              f"(undo option 3){RESET}")
        choice = prompt("Type 1 or 2, or press Enter to cancel: ")
        if choice == "2":
            target = original
        elif choice != "1":
            return
    elif not db or not os.path.isfile(db):
        target = original
    into_original = same_path(target, original)

    print()
    say("Which backup do you want to go back to? (newest first)")
    print()
    for i, folder in enumerate(folders, 1):
        ok, info = check_db(os.path.join(folder, "master.db"))
        tracks = f"{info} tracks" if ok else f"unreadable: {info}"
        when = datetime.fromtimestamp(os.path.getmtime(folder)).strftime(
            "%d.%m.%Y %H:%M")
        print(f"  {MANGO}[{i}]{RESET} {LIME}{os.path.basename(folder)}{RESET}"
              f"  ({when}, {tracks}, {backup_source_label(folder, original)})")
    print()

    choice = prompt("Type a number, or press Enter to cancel: ")
    if not choice:
        return
    if not choice.isdigit() or not 1 <= int(choice) <= len(folders):
        say("That is not one of the numbers above.")
        return
    folder = folders[int(choice) - 1]

    where = "your REAL rekordbox library" if into_original else "the working copy"
    if not yes(f"Replace {where} with the backup from {os.path.basename(folder)}?"):
        return

    wait_for_rekordbox_closed()
    try:
        safety = make_backup(target, prefix="before_restore_")
        say(f"Current state saved first: {safety}")
    except Exception as exc:
        say(f"Could not save the current state ({exc}).")
        if not yes("Restore anyway?"):
            return

    try:
        replace_db_file(target, os.path.join(folder, "master.db"))
    except Exception as exc:
        say(f"Restore failed: {exc}")
        return

    ok, info = check_db(target)
    if ok:
        say(f"Library restored ({info} tracks).")
    else:
        say(f"Restored, but the database could not be opened: {info}")
        say("Check the SQLCipher key (menu option 9).")

    # The leftover-file list no longer matches the restored library.
    update_settings(pending_quarantine=[])

    if into_original:
        if has_quarantined_files() and yes(
                "Move the quarantined music files back to where they were?"):
            unquarantine()
        if not same_path(original, db) and yes(
                "Make the working copy match the restored library? (recommended)"):
            copy_library(original)
            say("Working copy updated.")
    else:
        update_settings(pending_writeback=True)
        say("The working copy now differs from your rekordbox library.")
        say("Use option 3 if you want rekordbox to get this state too.")


# =====================================================================
#  Quarantine
# =====================================================================
def quarantine_files(files):
    target = quarantine_dir()
    os.makedirs(target, exist_ok=True)
    new_log = not os.path.exists(quarantine_log_path())
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    moved = 0

    with open(quarantine_log_path(), "a", newline="",
              encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        if new_log:
            writer.writerow(["Date", "OriginalPath", "QuarantinePath"])
        for src in files:
            if not os.path.isfile(src):
                continue
            base, ext = os.path.splitext(os.path.basename(src))
            dest, n = os.path.join(target, base + ext), 1
            while os.path.exists(dest):     # two files can share a name
                dest = os.path.join(target, f"{base} ({n}){ext}")
                n += 1
            try:
                shutil.move(src, dest)
            except Exception as exc:
                say(f"  Could not move {src}: {exc}")
                continue
            writer.writerow([now, src, dest])
            moved += 1
    return moved


def has_quarantined_files():
    if not os.path.exists(quarantine_log_path()):
        return False
    try:
        with open(quarantine_log_path(), encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f, delimiter=";"))
    except Exception:
        return False
    return any(os.path.isfile(r.get("QuarantinePath", "")) for r in rows)


def unquarantine():
    """Move every quarantined file back to its original place."""
    try:
        with open(quarantine_log_path(), encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f, delimiter=";"))
    except Exception:
        say("No quarantine log found.")
        return
    back, remaining = 0, []
    for r in rows:
        q, o = r.get("QuarantinePath", ""), r.get("OriginalPath", "")
        if os.path.isfile(q) and o and not os.path.exists(o):
            try:
                os.makedirs(os.path.dirname(o), exist_ok=True)
                shutil.move(q, o)
                back += 1
                continue
            except Exception as exc:
                say(f"  Could not move back {q}: {exc}")
        if os.path.isfile(q):
            remaining.append(r)
    with open(quarantine_log_path(), "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "OriginalPath",
                                               "QuarantinePath"], delimiter=";")
        writer.writeheader()
        for r in remaining:
            writer.writerow({k: r.get(k, "") for k in
                             ("Date", "OriginalPath", "QuarantinePath")})
    say(f"{back} files moved back.")
    if remaining:
        say(f"{len(remaining)} files stayed in quarantine "
            "(their original place is taken or not reachable).")


def offer_quarantine():
    """Offer to move files that only belonged to removed duplicates.

    Only called once the cleaned library is really in rekordbox.
    """
    settings = load_settings()
    pending = settings.get("pending_quarantine") or []
    files = [f for f in pending if os.path.isfile(f)]
    if not files:
        if pending:
            update_settings(pending_quarantine=[])
        return
    print()
    say(f"{len(files)} music files were only used by the removed duplicates.")
    say(f"They can be moved to the quarantine folder: {quarantine_dir()}")
    say("Nothing is deleted - you can empty that folder yourself later.")
    if yes("Move them there now?"):
        say(f"Moved {quarantine_files(files)} files. See quarantine_log.csv.")
        update_settings(pending_quarantine=[])
    else:
        say("OK. You can still do it later with menu option 4.")


# =====================================================================
#  Duplicate detection
# =====================================================================
def compare(a, b):
    """None = not a duplicate, else (certainty, reasons)."""
    if a["len"] and b["len"] and abs(a["len"] - b["len"]) > LENGTH_TOLERANCE:
        return None

    title_same = a["full"] == b["full"]
    if not (title_same or a["core"] == b["core"]):
        return None

    same_file = bool(a["npath"]) and a["npath"] == b["npath"]
    A, B = a["artists"], b["artists"]
    reasons = []

    if A and A == B:
        artist = "same"
    elif not A or not B:
        artist = "missing"
        reasons.append("one of them has no artist")
    elif A & B:
        artist = "partial"
        reasons.append("the artists are written differently")
    elif same_file:
        artist = "different"
        reasons.append("different artists, but it's the same file")
    else:
        return None

    if not title_same:
        reasons.append("the titles are slightly different (maybe a remix or edit)")
    if not a["len"] or not b["len"]:
        reasons.append("the length of one track is unknown")

    certain = artist == "same" and title_same and a["len"] and b["len"]
    return ("certain" if certain else "uncertain", reasons)


def ask_group(group, reasons, number):
    """Ask the user whether these tracks are the same song."""
    print()
    line()
    say(f"Question {number}: Are these the same song?", MANGO)
    say("Not sure because: " + ", ".join(sorted(reasons)))
    print()
    for i, track in enumerate(group, 1):
        print(f"  {MANGO}[{i}]{RESET} {LIME}{track['title']}{RESET}")
        print(f"      Artist: {track['artist'] or '(none)'}")
        print(f"      Length: {fmt_len(track['len'])}   "
              f"Cue points: {track['cues']}   "
              f"In playlists: {len(track['pls'])}")
        print(f"      File:   {os.path.basename(track['path']) or '(none)'}"
              + ("   <-- FILE MISSING" if not track["exists"] else ""))
        print()

    say("Same song?  y = yes   n = no   q = stop for now", MANGO)
    while True:
        answer = prompt("> ").lower()
        if answer in ("y", "n", "q"):
            break
        say("Please type y, n or q and press Enter.")

    if answer == "q":
        return "quit"
    if answer == "n":
        say("OK, they all stay in your library.")
        return {"merge": [], "keep": None}

    say("Which one should stay? Press Enter for [1] (recommended), "
        "or type a number:")
    while True:
        keep = prompt("> ") or "1"
        if keep.isdigit() and 1 <= int(keep) <= len(group):
            break
        say(f"Please type a number from 1 to {len(group)}, or press Enter.")

    say(f"OK, keeping [{keep}]. The others are removed and their "
        "playlists move to it.")
    return {"merge": [t["id"] for t in group], "keep": group[int(keep) - 1]["id"]}


def print_plan(plan, safe_files, limit=30):
    """Show which copy stays and which copies go, song by song."""
    safe = {normpath(p) for p in safe_files}
    print()
    say("Songs with duplicates:", MANGO)
    print()
    for nr, (keep, dups, _match) in enumerate(plan[:limit], 1):
        artist = keep["artist"] or "unknown artist"
        print(f"  {MANGO}{nr}.{RESET} {LIME}{keep['title']}{RESET}"
              f"  -  {artist}  ({fmt_len(keep['len'])})")
        cues, lists = keep["cues"], len(keep["pls"])
        print(f"      {LIME}keep{RESET}   "
              f"{os.path.basename(keep['path']) or '(no file)'}"
              f"   ({cues} {'cue' if cues == 1 else 'cues'}, in {lists} "
              f"{'playlist' if lists == 1 else 'playlists'})")
        for dup in dups:
            if not dup["exists"]:
                why = "file not found"
            elif normpath(dup["npath"]) in safe:
                why = "file can be quarantined"
            else:
                why = "file still used by a kept track"
            print(f"      {MANGO}remove{RESET} "
                  f"{os.path.basename(dup['path']) or '(no file)'}"
                  f"   ({why})")
        print()
    if len(plan) > limit:
        say(f"  ... and {len(plan) - limit} more songs - "
            "see duplicates_log.csv.")


def analyse(con, interactive=True):
    """Find duplicates, ask about unclear ones, write the reports.

    Returns (ref_tables, pairs, safe_files).
    """
    ref_tables = {}
    for (table,) in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        cols = [c[1] for c in con.execute(
            f'PRAGMA table_info("{table}")').fetchall()]
        if "ContentID" in cols and table != "djmdContent":
            ref_tables[table] = cols

    playlists = defaultdict(list)
    try:
        for cid, name in con.execute("""
            SELECT CAST(sp.ContentID AS TEXT), p.Name FROM djmdSongPlaylist sp
            JOIN djmdPlaylist p ON p.ID = sp.PlaylistID
            WHERE IFNULL(sp.rb_local_deleted,0)=0""").fetchall():
            playlists[cid].append(name)
    except Exception:
        pass

    cues = defaultdict(int)
    if "djmdCue" in ref_tables:
        try:
            for cid, n in con.execute("""
                SELECT CAST(ContentID AS TEXT), COUNT(*) FROM djmdCue
                WHERE IFNULL(rb_local_deleted,0)=0 GROUP BY ContentID""").fetchall():
                cues[cid] = n
        except Exception:
            pass

    tracks = {}
    for (cid, title, artist, path, length, bitrate, plays,
         rating) in con.execute("""
        SELECT CAST(c.ID AS TEXT), IFNULL(c.Title,''), IFNULL(a.Name,''),
               IFNULL(c.FolderPath,''), CAST(IFNULL(c.Length,0) AS INTEGER),
               CAST(IFNULL(c.BitRate,0) AS INTEGER),
               CAST(IFNULL(c.DJPlayCount,0) AS INTEGER),
               CAST(IFNULL(c.Rating,0) AS INTEGER)
        FROM djmdContent c LEFT JOIN djmdArtist a ON a.ID = c.ArtistID
        WHERE IFNULL(c.rb_local_deleted,0)=0""").fetchall():
        full, core = title_keys(title)
        tracks[cid] = dict(
            id=cid, title=title, artist=artist, path=path,
            npath=normpath(path), len=length, bitrate=bitrate, plays=plays,
            rating=rating, full=full, core=core, artists=artist_set(artist),
            exists=bool(path) and os.path.exists(path),
            pls=playlists[cid], cues=cues[cid],
        )
    say(f"Loaded {len(tracks)} tracks. Looking for duplicates...")

    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    buckets = defaultdict(list)
    for track in tracks.values():
        if track["full"]:
            buckets[("f", track["full"])].append(track["id"])
            buckets[("c", track["core"])].append(track["id"])

    checked = set()
    for ids in buckets.values():
        for x, y in combinations(ids, 2):
            pair = (min(x, y), max(x, y))
            if pair in checked:
                continue
            checked.add(pair)
            if compare(tracks[x], tracks[y]):
                parent[find(x)] = find(y)

    components = defaultdict(list)
    for tid in parent:
        components[find(tid)].append(tid)
    groups = sorted((g for g in components.values() if len(g) > 1),
                    key=lambda g: tracks[g[0]]["full"])

    decisions = load_json(decisions_path(), {})
    plan, undecided, stop, question_nr = [], 0, False, 0

    for group_ids in groups:
        group = sorted((tracks[i] for i in group_ids), key=score, reverse=True)
        results = [compare(a, b) for a, b in combinations(group, 2)]

        if all(r and r[0] == "certain" for r in results):
            plan.append((group[0], group[1:], "certain"))
            continue

        key = ",".join(sorted(t["id"] for t in group))
        decision = decisions.get(key)
        if decision and not all(i in tracks for i in decision["merge"]):
            decision = None

        if decision is None:
            if stop or not interactive:
                undecided += 1
                continue
            if question_nr == 0:
                say("")
                say("Some songs need your decision. Your answers are saved,")
                say("so you never have to answer the same question twice.")
            question_nr += 1
            reasons = set()
            for r in results:
                reasons.update(r[1] if r else ["not all of them match each other"])
            decision = ask_group(group, reasons, question_nr)
            if decision == "quit":
                stop = True
                undecided += 1
                continue
            decisions[key] = decision
            save_json(decisions_path(), decisions)

        if decision["merge"]:
            plan.append((tracks[decision["keep"]],
                         [tracks[i] for i in decision["merge"]
                          if i != decision["keep"]],
                         "confirmed"))

    removed = {t["id"] for _, dups, _ in plan for t in dups}
    still_used = {t["npath"] for t in tracks.values() if t["id"] not in removed}
    safe_files = []

    with open(log_csv_path(), "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Group", "Action", "Match", "ContentID", "Title",
                         "Artist", "Length", "BitRate", "FilePath",
                         "FileExists", "CuePoints", "Playlists", "KeptID",
                         "SafeToDeleteFile"])
        for gi, (keep, dups, match) in enumerate(plan, 1):
            writer.writerow([gi, "KEEP", match, keep["id"], keep["title"],
                             keep["artist"], fmt_len(keep["len"]),
                             keep["bitrate"], keep["path"], keep["exists"],
                             keep["cues"], " | ".join(keep["pls"]), "", ""])
            for dup in dups:
                if dup["npath"] in still_used:
                    safe = "NO - file still used by a kept track"
                elif not dup["exists"]:
                    safe = "NO - file not found"
                else:
                    safe = "YES"
                    safe_files.append(dup["path"])
                writer.writerow([gi, "REMOVE", match, dup["id"], dup["title"],
                                 dup["artist"], fmt_len(dup["len"]),
                                 dup["bitrate"], dup["path"], dup["exists"],
                                 dup["cues"], " | ".join(dup["pls"]),
                                 keep["id"], safe])

    safe_files = sorted(set(safe_files))
    with open(delete_list_path(), "w", encoding="utf-8") as f:
        f.write("\n".join(safe_files))

    pairs = [(dup["id"], keep["id"]) for keep, dups, _ in plan for dup in dups]
    certain = sum(1 for p in plan if p[2] == "certain")

    print()
    line("=")
    say("RESULT", MANGO)
    say(f"  {len(plan)} songs have duplicates -> "
        f"{len(pairs)} extra copies will be removed")
    say(f"    - {certain} songs: obvious duplicates")
    say(f"    - {len(plan) - certain} songs: you said yes")
    if undecided:
        say(f"  {undecided} questions not answered yet (those songs stay)")
    print_plan(plan, safe_files)
    say(f"  Lists saved in: {script_dir()}")
    say("    duplicates_log.csv   = list of all duplicates")
    say(f"    files_to_delete.txt  = {len(safe_files)} music files no longer needed")
    line("=")

    return ref_tables, pairs, safe_files


def apply_changes(con, ref_tables, pairs):
    """Remove duplicates. Playlist/tag/history entries move to the kept copy,
    cues and analysis data of the removed copy are deleted."""
    repoint = {t for t in ref_tables if t.startswith("djmdSong")}
    delete = set(ref_tables) - repoint
    unique_per = {"djmdSongPlaylist": "PlaylistID", "djmdSongMyTag": "MyTagID"}
    orphan_sql = """SELECT COUNT(*) FROM djmdSongPlaylist sp
                    WHERE NOT EXISTS (SELECT 1 FROM djmdContent c
                                      WHERE c.ID = sp.ContentID)"""
    orphans_before = con.execute(orphan_sql).fetchone()[0]
    affected = set()

    try:
        for dup, keep in pairs:
            for table in repoint:
                container = unique_per.get(table)
                if container and container in ref_tables[table]:
                    rows = con.execute(
                        f'SELECT ID, {container} FROM "{table}" WHERE ContentID=?',
                        (dup,)).fetchall()
                    for row_id, cont in rows:
                        already = con.execute(
                            f'SELECT 1 FROM "{table}" WHERE {container}=? '
                            f'AND ContentID=? AND IFNULL(rb_local_deleted,0)=0',
                            (cont, keep)).fetchone()
                        if already:
                            con.execute(f'DELETE FROM "{table}" WHERE ID=?',
                                        (row_id,))
                        else:
                            con.execute(
                                f'UPDATE "{table}" SET ContentID=? WHERE ID=?',
                                (keep, row_id))
                        if table == "djmdSongPlaylist":
                            affected.add(cont)
                else:
                    con.execute(
                        f'UPDATE "{table}" SET ContentID=? WHERE ContentID=?',
                        (keep, dup))
            for table in delete:
                con.execute(f'DELETE FROM "{table}" WHERE ContentID=?', (dup,))
            con.execute("DELETE FROM djmdContent WHERE ID=?", (dup,))

        for playlist_id in affected:
            ids = [r[0] for r in con.execute(
                "SELECT ID FROM djmdSongPlaylist WHERE PlaylistID=? "
                "ORDER BY TrackNo", (playlist_id,)).fetchall()]
            for i, song_id in enumerate(ids, 1):
                con.execute("UPDATE djmdSongPlaylist SET TrackNo=? WHERE ID=?",
                            (i, song_id))

        if con.execute(orphan_sql).fetchone()[0] > orphans_before:
            raise RuntimeError("some playlist entries would lose their track")

        con.commit()
        return len(affected)
    except Exception:
        con.rollback()
        raise


# =====================================================================
#  Startup
# =====================================================================
def guard_foreign_files():
    """Move away a library/settings that belong to another user account."""
    settings = load_settings()
    me = os.path.expanduser("~")
    if settings and settings.get("home") not in (None, me):
        dest = unique_folder(os.path.join(script_dir(), "from_other_user"))
        os.makedirs(dest)
        for name in ("master.db", "master.db-wal", "master.db-shm",
                     "settings.json", "decisions.json"):
            p = os.path.join(script_dir(), name)
            if os.path.exists(p):
                shutil.move(p, dest)
        say("This folder contained another person's library and settings.", MANGO)
        say(f"They were moved to: {dest}")
        say("Starting fresh with your own library.")
        print()
    settings = load_settings()
    settings["home"] = me
    save_settings(settings)


def startup_flow():
    """Welcome, check rekordbox, find the library, offer to copy it.

    Returns (db_path, original_library) or None when the user wants to quit.
    """
    global _color_i
    _color_i = 0

    print()
    line("=")
    say(f"  Welcome to {APP} v{VERSION} {PURPLE}(by djoshi){RESET}", MANGO)
    say("  Duplicate Track Remover for rekordbox 6/7")
    line("=")
    print()

    guard_foreign_files()

    settings = load_settings()
    db = settings.get("db") or master_db_path()
    original = settings.get("original_library")
    if not original or not os.path.isfile(original):
        found = find_rekordbox_library()
        if found:
            original = found
            update_settings(original_library=found)

    # ---------- a working copy already exists ----------
    if os.path.isfile(db):
        ok, info = check_db(db)
        if not ok:
            say("Your library copy could not be opened:")
            say(f"  {info}")
            say("If you changed the SQLCipher key, use menu option 9.")
            press_enter()
            return db, original

        say(f"Your library copy is ready ({info} tracks).")
        say(f"Working on: {db}")
        say(f"Backups:    {backups_dir()}")
        if original and not same_path(original, db):
            say(f"Original rekordbox library: {original}")

        if original_changed(original, db):
            print()
            say("rekordbox may have changed your library since this copy was made.",
                MANGO)
            say("If you write an old copy back, those changes would be lost.")
            if load_settings().get("pending_writeback"):
                say("Your copy also contains removed duplicates that were not")
                say("written back yet. A fresh copy discards them, but your")
                say("answers are saved, so option 2 is quick to redo.")
            if yes("Make a fresh copy now? (recommended)"):
                wait_for_rekordbox_closed()
                try:
                    db = copy_library(original)
                    ok, info = check_db(db)
                    say(f"Fresh copy ready ({info} tracks)." if ok
                        else f"Fresh copy could not be opened: {info}")
                except Exception as exc:
                    say(f"Could not copy the library: {exc}")
        press_enter()
        return db, original

    # ---------- no copy yet: walk the user through it ----------
    say("This program works on a copy of your rekordbox library,")
    say("never on the original. Nothing is changed without asking you.")
    print()

    wait_for_rekordbox_closed()

    if original and os.path.isfile(original):
        say(f"Found rekordbox library at: {original}")
    else:
        say("No rekordbox library found in the usual place.")
        while True:
            entered = clean_entered_path(
                prompt("Paste the full path to your master.db, then Enter: "))
            if not entered:
                return None
            if os.path.isdir(entered):
                entered = os.path.join(entered, "master.db")
            ok, info = check_db(entered)
            if ok:
                say(f"OK, found it ({info} tracks).")
                original = os.path.normpath(entered)
                break
            say(f"Could not open that file: {info}")

    print()
    say("Create a copy of your library in the rb ghostbuster folder?")
    say("rb ghostbuster never works on your original library.")
    if not yes("Create the copy now?"):
        say("No copy made. You can create one later with menu option 8.")
        press_enter()
        return "", original

    say("Copying, please wait...")
    try:
        db = copy_library(original)
    except Exception as exc:
        say(f"Could not copy the library: {exc}")
        press_enter()
        return "", original

    ok, info = check_db(db)
    if ok:
        say(f"Copy ready ({info} tracks): {db}")
        say("Your original library was not touched.")
    else:
        say(f"The copy was made but could not be opened: {info}")
        say("If your library uses a different SQLCipher key, use menu option 9.")
    press_enter()
    return db, original


# =====================================================================
#  Menu
# =====================================================================
def display_menu(db, original=None):
    global _color_i
    _color_i = 0
    clear_screen()

    print(set_color("=" * 60, MANGO))
    print(set_color(f"  {APP} - Duplicate Track Remover v{VERSION} "
                    f"{PURPLE}(by djoshi){RESET}", MANGO))
    print(set_color("=" * 60, MANGO))
    print()
    say("  NOTE: rb ghostbuster works on your library DATABASE (master.db).")
    say("  Your music files are NOT touched unless you move them to the")
    say("  quarantine folder yourself.")
    say("  " + "=" * 58)
    say("  TESTED ON WINDOWS ONLY - not verified on macOS or Linux")
    say("  " + "=" * 58)
    print()

    if db and os.path.isfile(db):
        if load_settings().get("pending_writeback"):
            say("  ! The copy has removed duplicates that are NOT in rekordbox",
                MANGO)
            say("  ! yet. Use option 3 to write them back.", MANGO)
            print()
    else:
        say("  Database: not set yet (use option 8)")
        print()

    print(set_color("  Please select an option:", LIME))
    print()
    print(f"  {MANGO}1{RESET}. {LIME}Test run - answer questions, show duplicates (library not changed){RESET}")
    print(f"  {MANGO}2{RESET}. {LIME}Full analysis - detect and resolve duplicates{RESET}")
    print(f"  {MANGO}3{RESET}. {LIME}Write the cleaned copy back to rekordbox{RESET}")
    print(f"  {MANGO}4{RESET}. {LIME}Quarantine folder (view, change, move files back){RESET}")
    print(f"  {MANGO}5{RESET}. {LIME}Backup database{RESET}")
    print(f"  {MANGO}6{RESET}. {LIME}Restore from backup (copy or rekordbox library){RESET}")
    print(f"  {MANGO}7{RESET}. {LIME}View current settings{RESET}")
    print(f"  {MANGO}8{RESET}. {LIME}Set/change database path{RESET}")
    print(f"  {MANGO}9{RESET}. {LIME}Set/change SQLCipher key{RESET}")
    print(f"  {MANGO}10{RESET}. {LIME}Forget saved answers (ask everything again){RESET}")
    print(f"  {MANGO}11{RESET}. {LIME}Quit{RESET}")
    print()
    print(set_color("=" * 60, MANGO))
    print()


# =====================================================================
#  Menu actions
# =====================================================================
def run_analysis(db, original, mode):
    """Option 1 (test) and 2 (full)."""
    if not db or not os.path.isfile(db):
        say("No database set yet. Use menu option 8 first.")
        return

    if mode == "full" and original_changed(original, db):
        say("Note: rekordbox may have changed your library since this copy", MANGO)
        say("was made. You won't be able to write the result back.", MANGO)
        say("Restart rb ghostbuster and accept the fresh copy first.")
        if not yes("Continue anyway?"):
            return

    try:
        con = open_db(db)
    except Exception as exc:
        say(f"Could not open the database: {exc}")
        say("If you changed the SQLCipher key, use menu option 9.")
        return

    applied = False
    safe_files = []
    try:
        try:
            ref_tables, pairs, safe_files = analyse(con)
        except Exception as exc:
            say(f"Could not read tracks: {exc}")
            say("This usually means the file is not a rekordbox master.db")
            say("or the SQLCipher key is not the standard one.")
            return

        if not pairs:
            say("Nothing to remove. Your library is clean!")
            return

        print()
        if mode == "test":
            say("TEST RUN: your library was not changed.")
            say("Use option 2 to remove these duplicates.")
            return
        if not yes(f"Remove these {len(pairs)} duplicates from your library now?"):
            say("OK. Nothing was changed.")
            return

        wait_for_rekordbox_closed()
        try:
            safety = make_backup(db)
        except Exception as exc:
            say(f"Could not create a safety backup: {exc}")
            if not yes("Continue without a backup?"):
                return
        else:
            say(f"Safety backup created: {safety}")

        say("Removing duplicates...")
        try:
            playlists = apply_changes(con, ref_tables, pairs)
        except Exception as exc:
            say(f"Nothing was changed: {exc}")
            return
        say(f"Done. Removed {len(pairs)} duplicates, updated {playlists} "
            "playlists.")
        applied = True
    finally:
        try:
            con.close()
        except Exception:
            pass

    if not applied:
        return

    # Remember which files can go once the result is really in rekordbox.
    settings = load_settings()
    pending = set(settings.get("pending_quarantine") or []) | set(safe_files)
    settings["pending_quarantine"] = sorted(pending)
    direct = same_path(original, db)
    if direct:
        settings["original_fingerprint"] = fingerprint(db)
        settings["pending_writeback"] = False
    else:
        settings["pending_writeback"] = True
    save_settings(settings)

    written = False
    if direct:
        written = True
        offer_quarantine()
    else:
        print()
        say("The duplicates are removed from the COPY. rekordbox doesn't see", MANGO)
        say("this yet - the copy has to be written back to rekordbox.", MANGO)
        if not original:
            say("The original rekordbox library is unknown - use option 8 first.")
        elif yes("Write the cleaned library back to rekordbox now?"):
            written = replace_original(db, original)

    print()
    line("=")
    if written:
        say("All done. You can open rekordbox now.")
        say("If something looks wrong, use option 6 (restore from backup).")
    else:
        say("Not written to rekordbox yet. Use option 3 when you're ready.")
        say("Music files are only offered for quarantine after that,")
        say("because rekordbox still uses them until then.")
    line("=")


def replace_original(db, original):
    """Option 3 - write the working copy back over the real library.

    Returns True on success.
    """
    print()
    line("!")
    say("  WARNING", MANGO)
    say("  This REPLACES your real rekordbox library with this copy.")
    say("  Only do this when you are happy with the result.")
    line("!")
    print()

    if not original:
        say("The original rekordbox library is unknown.")
        say("Use menu option 8 to point rb ghostbuster at it first.")
        return False
    if not db or not os.path.isfile(db):
        say("There is no library copy to write back yet.")
        return False
    if same_path(db, original):
        say("You are already working directly on the original file.")
        say("Nothing to replace.")
        return False

    say(f"Copy:     {db}")
    say(f"Original: {original}")
    print()
    wait_for_rekordbox_closed()

    if original_changed(original, db):
        say("STOP: rekordbox changed your original library after this copy", MANGO)
        say("was made. Replacing it now would undo those changes.", MANGO)
        say("Restart rb ghostbuster and accept the fresh copy,")
        say("then run option 2 again (your answers are saved).")
        return False

    ok, info = check_db(db)
    if not ok:
        say(f"The copy can't be opened ({info}). Not replacing anything.")
        return False

    answer = prompt("Type YES to replace your original library: ")
    if answer.upper() != "YES":
        say("Cancelled. Nothing was changed.")
        return False

    try:
        safety = make_backup(original, prefix="original_before_replace_")
        say(f"Original backed up first: {safety}")
    except Exception as exc:
        say(f"Could not back up the original: {exc}")
        if not yes("Replace anyway?"):
            return False

    try:
        replace_db_file(original, db)
    except Exception as exc:
        say(f"Could not replace the original library: {exc}")
        return False

    ok, info = check_db(original)
    if not ok:
        say(f"Replaced, but it could not be opened: {info}")
        say("Use option 6 > [2] to restore the original_before_replace_ backup.")
        return False

    say(f"Original library replaced ({info} tracks).")
    update_settings(original_fingerprint=fingerprint(original),
                    pending_writeback=False)
    offer_quarantine()
    return True


def quarantine_menu():
    """Option 4 - show the quarantine folder, change it, move files in/out."""
    folder = quarantine_dir()
    settings = load_settings()
    print()
    say(f"Quarantine folder: {folder}")
    files = []
    if os.path.isdir(folder):
        files = sorted(f for f in os.listdir(folder)
                       if os.path.isfile(os.path.join(folder, f)))
    if files:
        say(f"Files in quarantine ({len(files)}):")
        for name in files[:40]:
            print(f"  {LIME}- {name}{RESET}")
        if len(files) > 40:
            say(f"  ... and {len(files) - 40} more")
    else:
        say("The folder is empty.")

    pending = [f for f in settings.get("pending_quarantine") or []
               if os.path.isfile(f)]
    can_move = bool(pending) and not settings.get("pending_writeback")

    print()
    say("This is only for music files that are no longer used by any")
    say("track in your library. Nothing is ever deleted by rb ghostbuster.")
    print()
    if can_move:
        say(f"  M = move the {len(pending)} leftover duplicate files there now")
    if has_quarantined_files():
        say("  B = move all quarantined files back to where they were")
    say("  or type a new folder path, or press Enter to go back")
    answer = prompt("> ")
    if not answer:
        return
    if answer.lower() == "m" and can_move:
        offer_quarantine()
        return
    if answer.lower() == "b" and has_quarantined_files():
        if yes("Move all quarantined files back?"):
            unquarantine()
        return

    new_folder = clean_entered_path(answer)
    try:
        os.makedirs(new_folder, exist_ok=True)
    except Exception as exc:
        say(f"Could not use that folder: {exc}")
        return
    update_settings(quarantine_folder=new_folder)
    say(f"Quarantine folder set to: {new_folder}")


def backup_now(db):
    """Option 5."""
    if not db or not os.path.isfile(db):
        say("No database set yet. Use menu option 8 first.")
        return
    say("Creating backup...")
    try:
        say(f"Backup saved to: {make_backup(db)}")
    except Exception as exc:
        say(f"Backup failed: {exc}")


def show_settings(db, original):
    """Option 7."""
    settings = load_settings()
    print()
    say("Current settings:", MANGO)
    print()
    say(f"  Working copy:      {db or '(not set)'}")
    say(f"  Original library:  {original or '(not set)'}")
    say(f"  Backups folder:    {backups_dir()}")
    say(f"  Quarantine folder: {quarantine_dir()}")
    key = current_key()
    shown = key if len(key) <= 16 else key[:8] + "..." + key[-4:]
    say(f"  SQLCipher key:     {shown}")
    say(f"  Not written back:  {'yes' if settings.get('pending_writeback') else 'no'}")
    if not original:
        status = "unknown (original library not set)"
    elif same_path(original, db):
        status = "working directly on the original"
    elif original_changed(original, db):
        status = "no - make a fresh copy"
    else:
        status = "yes"
    say(f"  Copy up to date:   {status}")
    say(f"  Settings file:     {settings_path()}")


def set_database_path(db, original):
    """Option 8."""
    print()
    say(f"Current database: {db or '(not set)'}")
    print()
    entered = clean_entered_path(
        prompt("Path to master.db (drag the file here, then Enter): "))
    if not entered:
        return db, original

    if os.path.isdir(entered):
        entered = os.path.join(entered, "master.db")
    if not os.path.isfile(entered):
        say("That file does not exist.")
        return db, original

    ok, info = check_db(entered)
    if not ok:
        say(f"Could not open that file: {info}")
        say("Check that it is a rekordbox master.db and that the")
        say("SQLCipher key is correct (menu option 9).")
        return db, original

    say(f"OK, that library has {info} tracks.")
    if same_path(entered, master_db_path()):
        update_settings(db=master_db_path())
        return master_db_path(), original

    wait_for_rekordbox_closed()
    if not yes("Copy it into the rb ghostbuster folder and work on the copy?"):
        update_settings(db=entered, original_library=entered,
                        original_fingerprint=fingerprint(entered),
                        pending_writeback=False)
        say("Using the file directly - changes go straight into that library.")
        say("A backup is still made before every change.")
        return entered, entered

    try:
        new_db = copy_library(entered)
    except Exception as exc:
        say(f"Could not copy the library: {exc}")
        return db, original
    say(f"Working copy created: {new_db}")
    return new_db, entered


def change_key():
    """Option 9."""
    settings = load_settings()
    print()
    say("This rekordbox library is encrypted with SQLCipher.")
    say("The standard rekordbox 6/7 key is:")
    say(f"  {DEFAULT_KEY}", MANGO)
    print()
    say("You only need to change this if your library uses another key.")

    key = prompt("Enter the key (or press Enter for the standard one): ")
    if not key:
        key = DEFAULT_KEY

    db = settings.get("db") or master_db_path()
    if os.path.isfile(db):
        ok, info = check_db(db, key)
        if not ok:
            say(f"This key does not open your library: {info}")
            if not yes("Save it anyway?"):
                return
        else:
            say(f"Key works ({info} tracks).")

    settings["sqlcipher_key"] = key
    settings.pop("sqlcipher_locked", None)
    save_settings(settings)
    say("Key saved to settings.json. You can change it there any time.")


def forget_answers():
    """Option 10 - throw away the saved yes/no answers."""
    path = decisions_path()
    if not os.path.isfile(path):
        say("There are no saved answers yet - you will be asked everything.")
        return
    decisions = load_json(path, {}) or {}
    say(f"{len(decisions)} saved answers are stored in: {path}")
    say("Deleting them means option 1 and 2 ask every question again,")
    say("including the groups you answered 'no' to.")
    if not yes("Forget all saved answers?"):
        return
    stamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    backup = unique_folder(os.path.join(script_dir(), f"decisions_old_{stamp}"))
    backup = backup + ".json"
    try:
        os.replace(path, backup)
    except Exception as exc:
        say(f"Could not move the old answers aside: {exc}")
        return
    say(f"Old answers kept as: {os.path.basename(backup)}")
    say("You can delete that file yourself once you no longer need it.")


# =====================================================================
#  Main
# =====================================================================
def handle_menu_choice(choice, db, original):
    """Run one menu action. Returns (db, original), or None to quit."""
    if choice == "1":
        run_analysis(db, original, "test")
    elif choice == "2":
        run_analysis(db, original, "full")
    elif choice == "3":
        replace_original(db, original)
    elif choice == "4":
        quarantine_menu()
    elif choice == "5":
        backup_now(db)
    elif choice == "6":
        if (db and os.path.isfile(db)) or (original and os.path.isfile(original)):
            restore_backup(db, original)
        else:
            say("No database set yet. Use menu option 8 first.")
    elif choice == "7":
        show_settings(db, original)
    elif choice == "8":
        db, original = set_database_path(db, original)
    elif choice == "9":
        change_key()
    elif choice == "10":
        forget_answers()
    elif choice == "11":
        return None
    else:
        say("Please type a number from 1 to 11.")
        return db, original

    press_enter()
    return db, original


def _slice_char(angle):
    """Glyph for a line running along angle (screen y grows downwards)."""
    ox, oy = math.cos(angle), math.sin(angle)
    if abs(ox) > 2.4 * abs(oy):
        return "-"
    if abs(oy) > 2.4 * abs(ox):
        return "|"
    return "/" if ox * oy < 0 else "\\"


def _slice_row(cells):
    """Merge neighbouring cells of the same colour into one segment."""
    merged = []
    for char, colour in cells:
        if merged and merged[-1][1] == colour:
            merged[-1][0] += char
        else:
            merged.append([char, colour])
    return [(text, colour) for text, colour in merged]


def lime_slice(rind, pith, flesh, width=19, height=10, wedges=8):
    """A lime cut through the middle: peel, pith ring, wedges, pale core."""
    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
    radius = width / 2.0 - 0.5
    squash = 1.9                   # a cell is about twice as tall as it is wide
    rows = []
    for row in range(height):
        dy = (row - cy) * squash
        cells = []
        for col in range(width):
            dx = col - cx
            d = math.hypot(dx, dy)
            if d > radius:
                cells.append((" ", None))
                continue
            angle = math.atan2(dy, dx)
            if d > radius - 1.0:
                # the peel runs around the slice, not out from the middle
                cells.append((_slice_char(angle + math.pi / 2), rind))
            elif d > radius - 1.9:
                cells.append((".", pith))                  # pith ring
            elif d < 1.1:
                cells.append(("o", pith))                  # pale core
            elif abs(math.sin(wedges / 2 * angle)) < 0.16:
                cells.append((_slice_char(angle), pith))    # membranes
            else:
                cells.append((":" if (col * 2 + row) % 5 else ".", flesh))
        rows.append(_slice_row(cells))
    return rows


def goodbye():
    """A pineapple and a sliced lime, then a last line."""
    leaf_dark = "\033[38;5;28m"     # dark leaf green
    leaf = "\033[38;5;40m"          # bright leaf green
    gold = "\033[38;5;220m"         # pineapple flesh
    amber = "\033[38;5;178m"        # pineapple shading
    lime_rind = "\033[38;5;34m"     # lime peel
    lime_pith = "\033[38;5;255m"    # white pith and membranes
    lime_flesh = "\033[38;5;148m"   # juicy yellow-green flesh

    pineapple = [
        ("    \\|/    ", leaf),
        ("   - * -   ", leaf_dark),
        ("    /|\\    ", leaf),
        ("   ,---.   ", amber),
        ("  / . . \\  ", gold),
        (" |. . . .| ", amber),
        (" | . . . | ", gold),
        ("  \\ . . /  ", amber),
        ("   '---'   ", gold),
    ]
    lime = lime_slice(lime_rind, lime_pith, lime_flesh)

    def pad(row, width):
        """One cell: colour each piece, then fill up to the column width."""
        parts = row if isinstance(row, list) else [row]
        plain = "".join(text for text, _colour in parts)
        drawn = "".join(f"{colour}{text}{RESET}" if colour else text
                        for text, colour in parts)
        return drawn + " " * (width - len(plain))

    height = max(len(pineapple), len(lime))
    for fruit in (pineapple, lime):
        fruit.extend([[("", None)]] * (height - len(fruit)))

    print()
    for row in zip(pineapple, lime):
        print("  ".join(pad(part, width)
                        for part, width in zip(row, (14, 21))).rstrip(),
              flush=True)
    print()
    if load_settings().get("pending_writeback"):
        say("Note: your cleaned copy is NOT in rekordbox yet (option 3).",
            MANGO)
    say("come back anytime =)", MANGO)


_lock = None


def single_instance():
    """False if rb ghostbuster is already running from this folder."""
    global _lock
    try:
        _lock = open(os.path.join(script_dir(), ".rbg.lock"), "a+")
    except OSError:
        return True          # folder not writable - cannot lock, carry on
    try:
        if os.name == "nt":
            import msvcrt

            _lock.seek(0)
            msvcrt.locking(_lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def main():
    if not single_instance():
        say("rb ghostbuster is already running in another window.", MANGO)
        say("Close that window first - two copies must not change the")
        say("same library at the same time.")
        return
    try:
        started = startup_flow()
    except KeyboardInterrupt:
        return
    if started is None:
        return

    db, original = started
    while True:
        display_menu(db, original)
        choice = prompt("Enter your choice (1-11): ")
        if not choice:
            continue
        result = handle_menu_choice(choice, db, original)
        if result is None:
            goodbye()
            return
        db, original = result


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Stopped.")
    except Exception as exc:
        print()
        print("Something went wrong:", exc)
        print("Nothing is lost. Your backups are in:", backups_dir())
    try:
        input("\nPress Enter to close this window...")
    except EOFError:
        pass