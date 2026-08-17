Here is the complete setup guide tailored to all operating systems (**Linux**, **macOS**, and **Windows**).

Because several scripts in this codebase invoke `subprocess.Popen(["python", script_path])` (such as `JPVocMarkExtension` and `grammarminerlinker`), these setups ensure:
1. **Python 3.12** is installed along with **Tkinter** and **FFmpeg** (required by `pydub` and `whisperx`).
2. The command `python` directly resolves to `python3.12` system-wide and in virtual environments.
3. All dependencies (`whisperx`, `torch`, `pydub`, `pysrt`, `pykakasi`, `opencv-python`, `pandas`) are installed.

---

### 📦 Unified `requirements.txt`
First, create a `requirements.txt` file in your project root with the following content:

```text
torch
torchaudio
whisperx
pydub
pysrt
pykakasi
opencv-python
pandas
```

---

### 🐧 1. Linux (Ubuntu / Debian / Pop!_OS / Mint)

Run the following commands in your terminal from the root directory:

```bash
# 1. Update system and add Python 3.12 repository
sudo apt update && sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update

# 2. Install Python 3.12, Tkinter, Dev tools, FFmpeg, and OpenCV runtime libs
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3.12-tk \
                    ffmpeg libgl1 libglib2.0-0

# 3. Make 'python' and 'python3' permanently point to Python 3.12
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

# 4. Set up pip for Python 3.12
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# 5. Create and activate a Virtual Environment
python -m venv venv
source venv/bin/activate

# 6. Install PyTorch and Project Dependencies
pip install --upgrade pip setuptools wheel
# For NVIDIA GPU (CUDA 12.1):
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
# (OR for CPU only, uncomment the following line instead):
# pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

pip install -r requirements.txt
```

---

### 🐧 2. Linux (Fedora / RHEL / Rocky)

```bash
# 1. Install Python 3.12, Tkinter, FFmpeg, and dependencies
sudo dnf install -y python3.12 python3.12-devel python3.12-tkinter \
                    ffmpeg ffmpeg-devel mesa-libGL glib2

# 2. Make 'python' resolve to Python 3.12
sudo alternatives --set python /usr/bin/python3.12 2>/dev/null || sudo ln -sf /usr/bin/python3.12 /usr/bin/python

# 3. Create & Activate Virtual Environment
python3.12 -m venv venv
source venv/bin/activate

# 4. Install Dependencies
pip install --upgrade pip setuptools wheel
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

---

### 🐧 3. Linux (Arch Linux / Manjaro)

```bash
# 1. Update and install packages
sudo pacman -Syu --needed python tk ffmpeg mesa libglvnd

# 2. Ensure 'python' points to Python 3 (Arch defaults to latest Python)
# Create Virtual Environment
python -m venv venv
source venv/bin/activate

# 3. Install Dependencies
pip install --upgrade pip setuptools wheel
pip install torch torchaudio
pip install -r requirements.txt
```

---

### 🍏 4. macOS (Apple Silicon M1/M2/M3 & Intel)

Open Terminal and use [Homebrew](https://brew.sh/):

```bash
# 1. Install Python 3.12, Tkinter, and FFmpeg via Homebrew
brew install python@3.12 python-tk@3.12 ffmpeg

# 2. Unlink any older Python and force link Python 3.12
brew unlink python 2>/dev/null
brew link --overwrite --force python@3.12

# 3. Add to shell config (~/.zshrc) so 'python' alias always points to 3.12
echo 'export PATH="$(brew --prefix python@3.12)/libexec/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 4. Create and activate a Virtual Environment
python3.12 -m venv venv
source venv/bin/activate

# 5. Install Dependencies (Apple Silicon Metal support is enabled automatically by PyTorch)
pip install --upgrade pip setuptools wheel
pip install torch torchaudio
pip install -r requirements.txt
```

---

### 🪟 5. Windows (Windows 10 / 11)

Open **PowerShell (Run as Administrator)**:

#### Step A: Install Python 3.12 and FFmpeg via `winget`
```powershell
# 1. Install Python 3.12
winget install Python.Python.3.12 --override "/quiet PrependPath=1 Include_pip=1 Include_tcltk=1"

# 2. Install FFmpeg
winget install Gyan.FFmpeg

# 3. Refresh environment variables in current shell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

#### Step B: Set up the Environment & Packages
```powershell
# 1. Create Virtual Environment in project root
python -m venv venv

# 2. Activate Virtual Environment
.\venv\Scripts\Activate.ps1

# (If script execution is restricted on Windows, run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)

# 3. Install PyTorch (CUDA 12.1 for NVIDIA GPUs or CPU)
# For GPU:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
# For CPU only:
# pip install torch torchaudio

# 4. Install all project requirements
pip install -r requirements.txt
```

---

### ✅ Verification Check

To confirm that all system binaries, Python 3.12, and module dependencies are properly loaded, run this one-liner in your terminal/PowerShell:

```bash
python -c "import sys, cv2, pydub, pysrt, pykakasi, pandas, tkinter, whisperx; print(f'Ready! Python {sys.version.split()[0]} running all modules.')"
```

Expected output:
```text
Ready! Python 3.12.x running all modules.
```

---

### How CLI Package Managers Work Behind the Scenes:

#### 🪟 Windows (`winget`)
Windows 10 and 11 come with **`winget` (Windows Package Manager)** pre-installed by Microsoft. 
* When you run:
  ```powershell
  winget install Python.Python.3.12 --override "/quiet PrependPath=1 Include_pip=1 Include_tcltk=1"
  ```
  `winget` automatically pulls the official installer directly from Python's official release servers, silently runs the installer in the background, enables Tkinter (`Include_tcltk=1`), and **automatically adds Python to your Windows System Environment PATH** (`PrependPath=1`) so you never have to manually edit environment variables.

#### 🐧 Linux (`apt`, `dnf`, `pacman`)
On Linux, almost no one downloads software from websites. Linux uses native system repositories:
* `apt` (Ubuntu/Debian) or `dnf` (Fedora) connects directly to verified software mirrors and installs Python along with its system headers and C-libraries in seconds.

#### 🍏 macOS (`brew`)
On Mac, **Homebrew** (`brew`) is the community-standard package manager:
* It downloads the compiled bottle/binary for your specific chip architecture (Intel or Apple Silicon M1/M2/M3) and sets up all symlinks automatically.

#### Why doing it via CLI is better:
1. **Zero installer wizard mistakes:** You avoid common errors like forgetting to check the *"Add python.exe to PATH"* checkbox on Windows.
2. **Installs System Tools in parallel:** Tools like **FFmpeg** (which are required for `pydub` and `whisperx` audio/video cutting) would normally require downloading `.zip` files and manually messing with Windows Environment Variables—`winget install Gyan.FFmpeg` or `brew install ffmpeg` does it in 3 seconds.
3. **100% Reproducible:** You can paste the script into any new computer or virtual machine and have the entire environment ready to run without manual setup.