# PACEMAKER DCM - Setup Guide

## Prerequisites
- Python 3.13 or higher
- pip (Python package installer)

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/nihalinel/PACEMAKER_DCM.git
cd PACEMAKER_DCM
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Installation
Run the login application:
```bash
python -m gui.login
```

## Required Dependencies

The following packages will be installed automatically:
- **bcrypt** - Secure password hashing
- **pydicom** - DICOM medical imaging format support
- **numpy** - Numerical computing
- **matplotlib** - Plotting and graphing
- **tzlocal** - Timezone utilities
- **pillow** - Image processing

**Note:** `sqlite3` and `tkinter` come built-in with Python and don't need separate installation.

## Troubleshooting

### Missing Module Errors
If you see `ModuleNotFoundError`, ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### PATH Warnings
If you see warnings about Scripts not being on PATH:
- **Windows**: Add `C:\Users\<YourUsername>\AppData\Roaming\Python\Python313\Scripts` to your PATH
- **Mac/Linux**: Add `~/.local/bin` to your PATH

### Permission Errors
If you get permission errors, try:
```bash
pip install --user -r requirements.txt
```

## Project Structure
```
PACEMAKER_DCM/
├── auth/              # Authentication module
├── data/              # User parameter storage
├── dicom/             # DICOM file handling
├── gui/               # GUI modules
│   ├── login.py
│   ├── main_interface.py
│   └── patient_select.py
├── requirements.txt   # Dependency list
└── main.py           # Entry point
```

## Running the Application

### Option 1: Run as Module
```bash
python -m gui.login
```

### Option 2: Run Main Script
```bash
python main.py
```

## Support
For issues or questions, contact Nihal Inel (inela@mcmaster.ca) or Elijah James (jamese13@mcmaster.ca)