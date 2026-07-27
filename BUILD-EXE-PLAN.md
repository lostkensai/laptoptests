# Plan: Building "Laptop Battery Test.exe"

This document explains how to compile the battery test (`browse.py`) into a
standalone Windows program that end users can run **without installing
Python or anything else**. The build must be done **on a Windows 10/11
computer** (PyInstaller cannot cross-compile from Mac/Linux).

## TL;DR for the person building it

1. `git pull` this repository (or download it) onto a Windows computer.
2. Double-click **`Build EXE.bat`** in the repo folder and wait 5–15 minutes.
3. The finished product is the folder **`dist\Laptop Battery Test\`**.
4. Right-click that folder → *Compress to ZIP file* → send the zip to the
   end user. They unzip it anywhere and double-click
   **`Laptop Battery Test.exe`**. Nothing to install, no internet needed
   to set up (the sites being browsed still need internet, of course).

## What the build produces

- A **one-folder** (not one-file) PyInstaller build named
  `Laptop Battery Test`, containing `Laptop Battery Test.exe` plus its
  support files **and a bundled copy of Chromium** (~350–400 MB total).
  One-folder mode is deliberate: it starts faster and triggers far fewer
  antivirus false positives than `--onefile`.
- The exe keeps its console window open on purpose — closing that black
  window is how the user stops the test.

## Requirements on the build machine

- Windows 10 or 11
- Python 3.10–3.12 from python.org (tick *"Add python.exe to PATH"* when
  installing). If the machine already ran `Setup.bat`, Python is present.
- Internet connection and ~2 GB free disk space during the build.

## How it works (for the curious)

`Build EXE.bat` automates these steps:

1. Creates a dedicated build environment `.venv-build` (kept separate from
   the `.venv` that `Setup.bat` makes, because step 3 installs the browser
   in a non-standard place).
2. Installs `playwright` and `pyinstaller` into it.
3. Sets `PLAYWRIGHT_BROWSERS_PATH=0` and runs `playwright install chromium`.
   That environment variable makes Playwright download Chromium **inside its
   own package folder** instead of the user's cache — which is what lets
   PyInstaller bundle it.
4. Runs PyInstaller:

   ```
   pyinstaller --noconfirm --clean --onedir ^
       --name "Laptop Battery Test" ^
       --collect-all playwright ^
       browse.py
   ```

   `--collect-all playwright` copies the whole Playwright package —
   including the Chromium downloaded in step 3 — into the build.

`browse.py` contains a matching runtime check: when it detects it is running
as a frozen exe, it sets `PLAYWRIGHT_BROWSERS_PATH=0` so Playwright looks
for Chromium inside the app folder. When run normally (via `Setup.bat` /
the `.venv`), behaviour is unchanged.

Build output folders (`.venv-build/`, `build/`, `dist/`, `*.spec`) are
git-ignored — commit the *recipe*, not the 400 MB result.

## Things to know before distributing

- **SmartScreen:** the exe is unsigned, so the first run shows
  *"Windows protected your PC"* → the user clicks **More info → Run anyway**.
  Making this warning disappear requires a paid code-signing certificate;
  for internal use, telling users about "Run anyway" is the normal approach.
- **Antivirus:** PyInstaller exes occasionally get false-positive flagged.
  If that happens, the fix is usually to rebuild after excluding the folder,
  or to whitelist the exe in the AV console.
- **Desktop shortcut:** with the exe there is no setup step to create one.
  The user can right-click `Laptop Battery Test.exe` →
  *Send to → Desktop (create shortcut)* if they want one.
- **Scope:** this builds only the battery test (`browse.py`). The LLM and
  speech benchmarks are not included — they depend on Ollama and a compiled
  whisper.cpp, which cannot be bundled this way.

## Troubleshooting the build

| Symptom | Fix |
|---|---|
| "Python was not found" | Install Python from python.org, tick *Add python.exe to PATH*, rerun. |
| Build fails partway | Delete `.venv-build/`, `build/`, `dist/`; check internet; rerun `Build EXE.bat`. |
| Exe builds but says it can't find Chromium | Step 3 ran without `PLAYWRIGHT_BROWSERS_PATH=0` at some point. Delete `.venv-build/` and rerun the whole script. |
| AV deletes files mid-build | Add the repo folder to antivirus exclusions, rerun. |

## Alternative: build in the cloud instead

If building on a Windows PC ever becomes a hassle, a GitHub Actions
workflow on `windows-latest` can run these exact steps and attach the
zipped build to a GitHub release automatically — no Windows machine needed.
Ask for it if wanted; it is intentionally not set up yet.
