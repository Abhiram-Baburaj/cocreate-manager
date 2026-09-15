# CoCreate Manager

A Python-based application to ease the use of pirated CoCreate 2013.
Features:
* **No Python Required:** Run the application directly without needing to install Python, manage dependencies, or set up virtual environments.
* **Silent Execution:** The application runs seamlessly in the background and hides itself in the taskbar tray.
* **Automatic License Server Launcher:** This application constantly launches the license server at set intervals to keep it running in the background.
* **Automatic time changer:** This application automatically changes the year to 2013 to comply with the license server.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Abhiram-Baburaj/cocreate-manager
   cd cocreate-manager
   ```

2. **Set up and activate the virtual environment:**
   ```bash
   python -m venv .venv
   
   # On Windows:
   .\.venv\Scripts\activate
   
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Execute the main script:
```bash
python cocreate-manager.pyw
```
*(Note: `.pyw` extensions run without opening a console window on Windows.)*

## Building the Executable

This project uses PyInstaller to compile into a standalone application.

1. Ensure your virtual environment is active.
2. Run the build command using the provided specification file:
   ```bash
   pyinstaller cocreate-manager.spec
   ```
   or
   use the command in `buildcommand` file
3. The compiled executable will be available in the `dist/` directory.
