# rb ghostbuster v0.2.0

by **djoshi**

Remove duplicate tracks from your rekordbox 6/7 music library — safely, with backups and undo.

Built on [pyrekordbox](https://github.com/dylanljones/pyrekordbox) by Dylan Jones and [sqlcipher3-wheels](https://pypi.org/project/sqlcipher3-wheels/) for encrypted SQLite access.

**Download:** [rb-ghostbuster-main.zip](https://github.com/d-j-o-s-h-i/rb-ghostbuster/archive/refs/heads/main.zip) · Repo: https://github.com/d-j-o-s-h-i/rb-ghostbuster

> ⚠️ **Important:** Close rekordbox **and rekordboxAgent** before running this tool. It needs exclusive access to your `master.db` database.

> ⚠️ **Platform Notice:** rb ghostbuster has been **tested on Windows only**. macOS and Linux support is **not verified** — the script may work but has not been tested on those platforms.

> ⚠️ **Cloud Library Sync:** turn off rekordbox's Cloud Library Sync (and any other sync to a second device) while you clean your library. rb ghostbuster writes straight into `master.db`; a sync running at the same time can bring removed tracks back.

---

## What it does

rb ghostbuster scans your rekordbox library for duplicate tracks using title, artist, length, and other metadata. It groups duplicates together and lets you pick which one to keep. The rest are safely quarantined (moved to a `quarantine/` folder — not deleted), and playlist entries, tags and play history are reassigned to the kept track. An undo option is available if you change your mind.

**Cue points do not move.** When a copy is removed, its cue points, beat grid and analysis data go with it — the copy you keep keeps its own cues. That is why the tool recommends the copy with the most cue points. Pick carefully if two copies have very different cues.

Built on other people's work: the table and column names come from [pyrekordbox](https://github.com/dylanljones/pyrekordbox) by Dylan Jones, which documents the rekordbox 6/7 database schema; [sqlcipher3](https://github.com/coleifer/sqlcipher3) by Charles Leifer, packaged as the prebuilt [sqlcipher3-wheels](https://pypi.org/project/sqlcipher3-wheels/) by laggykiller, opens the encrypted `master.db` and is installed automatically on first run. Everything else — duplicate matching, quarantine, backups, undo, the interface — is the Python standard library. Thanks to both. Lemme know how we can integrate it into your tool =)

---

## Installation (noob-friendly)

You only need **Python**. Everything else installs automatically the first time you run it.

### Step 1: Install Python (if you don't have it)

**Windows:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download the latest Python 3 installer for Windows
3. **Important:** Check the box **"Add Python to PATH"** during installation
4. Click Install Now

**macOS / Linux:**
Python is usually already there. You check it in a text window called **Terminal** — that is just an app where you type commands and press Enter.

1. Open **Terminal**:
   - **macOS:** press `Cmd + Space`, type `Terminal`, press Enter. (Or Finder → Applications → Utilities → Terminal.)
   - **Linux:** press `Ctrl + Alt + T`, or open your apps menu and search for **Terminal**.
2. Type this in the Terminal window and press Enter:

   ```bash
   python3 --version
   ```

3. Look at the answer:
   - **`Python 3.x.x`** (for example `Python 3.11.4`) → you are ready, go to Step 2.
   - **`command not found`** → install Python first from [python.org/downloads](https://www.python.org/downloads/) (macOS), or from your app store / package manager (Linux), then run the command again.

---

### Step 2: Download rb ghostbuster

1. Open **https://github.com/d-j-o-s-h-i/rb-ghostbuster** in your browser
2. Click the green **Code** button (top right of the file list) → **Download ZIP**
3. Extract the ZIP to a folder you'll remember — right-click the ZIP → **Extract All** on Windows
4. Open that folder

That is the whole download: no installer, no admin rights, nothing outside the folder.

**Direct link to the ZIP:**
https://github.com/d-j-o-s-h-i/rb-ghostbuster/archive/refs/heads/main.zip

<details>
<summary>Prefer git?</summary>

```bash
git clone https://github.com/d-j-o-s-h-i/rb-ghostbuster.git
cd rb-ghostbuster
```

To update an existing clone later: `git pull`. Your `master.db`, `settings.json`, `decisions.json`, `backups/` and `quarantine/` are ignored by git, so a pull never touches your library or your answers.

</details>

---

### Step 3: Run the tool

**Windows (easiest):**
Open the rb ghostbuster folder and **double-click `rb ghostbuster.pyw`**. A window opens by itself.

If double-clicking does nothing, open the folder, click the address bar, type `cmd` and press Enter, then run:
```cmd
python "rb ghostbuster.pyw"
```

**macOS / Linux:**
1. Open **Terminal** (macOS: `Cmd + Space`, type `Terminal`, Enter — Linux: `Ctrl + Alt + T`).
2. Type `cd ` (with a space after `cd`), then **drag the rb ghostbuster folder** from Finder or your file manager into the Terminal window. Press Enter. You are now inside that folder.
3. Type this and press Enter:

   ```bash
   python3 "rb ghostbuster.pyw"
   ```

   The tool runs right there in the Terminal. Leave that window open while it works.

The first time you run it, the missing library (`sqlcipher3-wheels`) installs automatically. On Linux and on Homebrew Python, the system may block normal installs with an `externally-managed-environment` message; rb ghostbuster handles this on its own — it retries with a user-only override and, if that is still refused, creates a private `.venv` folder inside the rb ghostbuster folder. Nothing is installed system-wide.

You'll see a welcome screen that:

1. Asks if rekordbox is closed (it must be)
2. Looks for your rekordbox library at the standard location
3. Offers to copy `master.db` into the project folder
4. Then opens the main menu

---

### Step 4: Use the tool

The database file (`master.db`) lives in the same folder as the script. If rb ghostbuster found your rekordbox library on startup, it offers to copy it there. If not, use **menu option 8** to point to your `master.db` manually.

Wherever you move the project folder, the database and settings stay with it.

---

## What the screens look like

### Welcome screen

```
============================================================
  Welcome to rb ghostbuster v0.2.0 (by djoshi)
  Duplicate Track Remover for rekordbox 6/7
============================================================

This program works on a copy of your rekordbox library,
never on the original. Nothing is changed without asking you.

Is rekordbox completely closed? (y/n): y

Found rekordbox library at: C:\Users\<name>\AppData\Roaming\Pioneer\rekordbox\master.db

Create a copy of your library into the
rb ghostbuster folder?
rb ghostbuster is never working on your original library.
Create the copy now? (y/n): y
Copying, please wait...
Copy ready (1234 tracks): C:\path\to\rb ghostbuster\master.db
Your original library was not touched.
```

### Main menu

```
============================================================
  rb ghostbuster - Duplicate Track Remover v0.2.0 (by djoshi)
============================================================

  NOTE: rb ghostbuster works on your library DATABASE (master.db).
  Your music files are NOT touched unless you move them to the
  quarantine folder yourself.
  ==========================================================
  TESTED ON WINDOWS ONLY - not verified on macOS or Linux
  ==========================================================

  Please select an option:

  1. Test run - answer questions, show duplicates (library not changed)
  2. Full analysis - detect and resolve duplicates
  3. Write the cleaned copy back to rekordbox
  4. Quarantine folder (view, change, move files back)
  5. Backup database
  6. Restore from backup (copy or rekordbox library)
  7. View current settings
  8. Set/change database path
  9. Set/change SQLCipher key
  10. Forget saved answers (ask everything again)
  11. Quit

============================================================

Enter your choice (1-11): _
```

---

## Menu Options

| # | Option | What it does |
|---|--------|--------------|
| 1 | Test run | Loads your library, finds all duplicate groups, shows them, and asks only about tracks it is unsure of. Your answers are saved for option 2, but **the library is never changed** |
| 2 | Full analysis | Same detection, then asks which track to keep in each unclear group, prints every group with the copy that stays and the copies that go, applies the removals and moves playlists, tags and play history to the kept track |
| 3 | Write the cleaned copy back to rekordbox | Copies your cleaned library over the original rekordbox `master.db`. It asks you to type `YES` first (WARNING: destructive action) |
| 4 | Quarantine folder | See quarantined tracks, set a custom quarantine location, move the leftover duplicate files there, or move quarantined files back |
| 5 | Backup database | Creates a timestamped backup before making changes |
| 6 | Restore from backup | Restores your database from a previous backup — into the working copy, or into the real rekordbox library to undo option 3 |
| 7 | View current settings | Shows paths, backup folder, quarantine folder, key status and whether the copy is up to date |
| 8 | Set/change database path | Point the tool at another `master.db` (and offer to copy it into the project folder) |
| 9 | Set/change SQLCipher key | Change the encryption key for your rekordbox database |
| 10 | Forget saved answers | Moves `decisions.json` aside so options 1 and 2 ask every question again, including the ones you answered "no" to |
| 11 | Quit | Exits the program |

---

## How Duplicate Detection Works

1. Loads all tracks from your rekordbox `master.db`
2. Normalizes titles (strips accents, lowercases, removes special chars)
3. Matches tracks by full title OR core title (ignores remix/edit tags in parentheses)
4. Checks artist similarity, file path, and track length (±3 seconds tolerance)
5. Groups duplicates together using a smart union-find algorithm
6. Suggests which copy to keep and presents the groups to you

The recommended copy is the one whose file still exists, then the one with the most cue points, then the one in more playlists, then the higher bitrate. If two copies are still identical in every respect, a name like `Track (1).mp3` or `Track - Copy.mp3` loses to `Track.mp3`, the shorter file path wins after that, and the file you imported first wins last of all.

Decisions are saved in `decisions.json` so you're never asked about the same group twice. If you change your mind, menu option 10 forgets them.

---

## Safety Features

| Feature | Description |
|---------|-------------|
| **Backup first** | A timestamped backup of `master.db` is created before any changes |
| **Backup format** | One folder per backup, named day-month-year-time (e.g. `backups/26-10-2026_17-30-00/`), containing `master.db` |
| **Backup cleanup** | The newest 10 backups are kept, and the newest 10 safety copies of your real library are counted separately, so routine backups can never push those out |
| **Safety backup** | When replacing the original rekordbox library, a safety backup of the original is made first |
| **Atomic write-back** | The cleaned library is written to a temporary file, checked, and only then swapped in — an interrupted write can never leave a half-written `master.db` |
| **Quarantine, not delete** | Music files that only the removed copies used are moved to `quarantine/`, never deleted |
| **Undo** | Option #6 restores your database from any backup |
| **Test run** | Option #1 shows duplicates and never modifies your library |
| **Playlist integrity** | Playlist entries, tags and play history move to the kept track; entries are renumbered and checked for orphans before saving |
| **One window at a time** | A second copy of the program refuses to start, so two windows can never edit the same library |

Cue points, beat grids and analysis data of a **removed** copy are deleted along with it. Playlists, tags and play history are moved to the kept copy.

---

## File Structure

```
rb ghostbuster/
├── rb ghostbuster.pyw    # Main script (double-click to run)
├── README.md             # This file
├── LICENSE               # MIT license
├── .gitignore            # Keeps your library out of git
├── master.db             # Your rekordbox database copy (created on first run)
├── settings.json         # Your saved settings (created at runtime; contains your SQLCipher key)
├── .rbg.lock             # "one window at a time" lock (created at runtime)
├── decisions.json        # Your duplicate decisions (created at runtime)
├── duplicates_log.csv    # Log of actions taken
├── files_to_delete.txt   # Files marked for removal
├── quarantine_log.csv    # Which music file went where in quarantine
├── backups/              # Timestamped database backups (day-month-year-time format)
├── quarantine/           # Removed tracks go here (safe, not deleted)
├── config/
│   └── settings.example.json  # Example settings file
└── .venv/                # Optional: private Python env, only created if a normal install is blocked
```

`settings.json` holds your SQLCipher key and your paths. It is yours — don't share or commit it.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `"python" is not recognized` | Install Python and check "Add Python to PATH" during installation |
| Database not found | Close rekordbox, then use menu option 8 to point to your `master.db` |
| Can't open database | rekordbox and rekordboxAgent must be **closed** before running rb ghostbuster |
| Could not read tracks | The file is not a rekordbox `master.db`, or your library uses a different SQLCipher key (menu option 9) |
| Double-click doesn't open a window | Run from terminal instead: `python "rb ghostbuster.pyw"` |
| "already running in another window" | Close the other rb ghostbuster window — the lock is released when it exits |
| Asked about the same songs again | Menu option 10 restores the questions; delete `decisions_old_*.json` to drop the old answers for good |

---

## License

MIT License — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

**Stay safe:** Always keep a backup of your rekordbox library before making bulk changes. rb ghostbuster creates one automatically, but an extra copy never hurts.
