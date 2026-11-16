# Easy Cutter

A lightweight desktop app (Python + Tkinter) for saving a range of a video as a separate, frame-accurate clip.

## Requirements

- **Python 3.10 or newer** with Tkinter.
  - Windows: the installer from [python.org](https://www.python.org/downloads/) includes Tkinter. Tick **"Add python.exe to PATH"** during setup.
  - macOS: the python.org installer includes Tkinter. With Homebrew, also run `brew install python-tk`.
  - Linux (Debian/Ubuntu): `sudo apt install python3 python3-venv python3-tk`
- **Git** (only if you clone the repository instead of downloading the ZIP).
- **ffmpeg** does not need to be installed separately. If there is no `ffmpeg` on your PATH, the copy bundled with the `imageio-ffmpeg` package is used.

Check your Python version:

```bash
python --version
```

On macOS and Linux the command is often `python3` instead of `python`. Use it in all steps below until the virtual environment is activated.

## Installation with a virtual environment (venv)

A virtual environment keeps the app's packages separate from the rest of your system.

### 1. Get the code

```bash
git clone https://github.com/Ferocit/EasyCutter.git
cd EasyCutter
```

Alternatively, download the ZIP on GitHub (**Code → Download ZIP**), extract it and open a terminal in the extracted folder.

### 2. Create the virtual environment

```bash
python -m venv .venv
```

This creates a folder named `.venv` inside the project.

### 3. Activate it

Windows (Command Prompt):

```bat
.venv\Scripts\activate.bat
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell refuses to run the script, allow local scripts for your user once with `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` and try again.

macOS / Linux:

```bash
source .venv/bin/activate
```

When it is active, your prompt starts with `(.venv)`. From now on `python` and `pip` refer to the virtual environment.

### 4. Install the dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This installs [PyAV](https://pyav.basswood-io.com/), Pillow, imageio-ffmpeg and tkinterdnd2.

### 5. Start the app

```bash
python -m easy_cutter
```

Or open a video right away:

```bash
python -m easy_cutter path/to/video.mp4
```

### Starting it again later

Open a terminal in the project folder, activate the environment (step 3) and run `python -m easy_cutter`. To leave the virtual environment, type `deactivate`.

### Windows shortcut: `start.bat`

On Windows you can simply double-click `start.bat`. On the first run it creates `.venv` and installs the dependencies; after that it starts the app directly without a console window. Any video path passed to it (for example by dragging a file onto `start.bat`) is opened in the app.

### Updating

```bash
git pull
pip install -r requirements.txt
```

(with the virtual environment activated)

## Usage

- **Open video**, or drag a video file into the window. This also works when a video is already loaded.
- On the left you see the whole video with play/pause and a position slider; on the right the first and last frame of the selected range.
- Drag the range (default 5 s) along the timeline or click next to the selection. With the timeline focused, the arrow keys move it by 0.1 s, with Shift by 1 s.
- Start and length can also be typed in as numbers.
- **−1 Frame / +1 Frame** below the preview images move the start or the end by exactly one frame. Holding the button down repeats the step (about 20 frames per second). The other boundary stays where it is. The buttons become active once the frame index has been built (in the background while loading).
- **Start = current position** uses the player's position as the start of the range.
- **Play range** plays only the selected range.
- **Save clip** exports it as MP4 (H.264/AAC).
- **Save to: Choose folder …** sets a fixed output folder. Clips are then saved there without asking. If the file name already exists, `_2`, `_3` etc. is appended. **Ask every time** switches back to the save dialog. The folder is stored in `%APPDATA%\EasyCutter\settings.json` (on macOS/Linux in `~/.config/EasyCutter/settings.json`).

The range contains all frames from `Start` up to, but not including, `Start + Length`. At 25 fps and a range from 3 s to 8 s, the last frame is therefore the one at 7.96 s. The exported clip contains exactly the frames shown on the right.

## How it works and limitations

- Frames are decoded with [PyAV](https://pyav.basswood-io.com/); the export uses ffmpeg.
- For the frame buttons, the actual timestamps of all frames are read from the container when loading (without decoding). This keeps the steps exact even with variable frame rates. For very large files this can take a few seconds.
- The export re-encodes the video so the cut does not snap to keyframes. This is slower than cutting without re-encoding.
- Playback in the main window has no sound and is only meant for orientation. The exported clip includes the audio.
- Drag & drop uses the `tkinterdnd2` package. If it is missing, the app runs without drag & drop.

## Tests

With the virtual environment activated:

```bash
pip install pytest
pytest
```
