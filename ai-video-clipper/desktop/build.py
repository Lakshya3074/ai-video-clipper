#!/usr/bin/env python3
"""
Build script for AI Video Clipper Desktop App

This script:
1. Bundles the Python backend as a Tauri sidecar
2. Builds the React frontend with Vite
3. Compiles the Tauri app for your platform

Prerequisites:
- Python 3.10+ with pip
- Node.js 18+ with npm
- Rust (for Tauri) - install via rustup.rs
- FFmpeg installed on system (or bundled)
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def run_cmd(cmd, cwd=None, check=True):
    """Run a shell command."""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(
        cmd if isinstance(cmd, list) else cmd.split(),
        cwd=cwd,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise RuntimeError(f"Command failed: {result.returncode}")
    return result

def get_platform():
    """Get the current platform identifier."""
    system = platform.system().lower()
    arch = platform.machine().lower()

    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return "linux"

def build_backend():
    """Build the Python backend as a standalone executable."""
    print("\n=== Building Python Backend ===")

    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("Backend directory not found. Please run from desktop folder.")
        return False

    # Create sidecar directory
    sidecar_dir = Path("src-tauri/binaries")
    sidecar_dir.mkdir(parents=True, exist_ok=True)

    # Install PyInstaller
    run_cmd([sys.executable, "-m", "pip", "install", "pyinstaller", "--quiet"])

    # Install backend dependencies
    run_cmd([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt", "--quiet"])

    # Create entry point for the sidecar
    sidecar_entry = Path("sidecar_main.py")
    sidecar_entry.write_text("""
import sys
import os
from pathlib import Path

# Add the bundled resources to path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(__file__).parent

# Change to the backend directory
os.chdir(base_path / "backend")

# Import and run the FastAPI app
import uvicorn
from main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"Starting backend on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
""")

    # Build with PyInstaller
    platform_name = get_platform()
    spec_name = f"sidecar_main_{'mac' if platform_name == 'macos' else platform_name}"

    run_cmd([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "sidecar",
        "--add-data", f"backend{os.pathsep}backend",
        "--hidden-import", "faster_whisper",
        "--hidden-import", "yt_dlp",
        "--hidden-import", "cv2",
        "--hidden-import", "mediapipe",
        "sidecar_main.py"
    ])

    # Copy the binary to Tauri's expected location
    dist_binary = Path("dist/sidecar")
    if platform_name == "windows":
        dist_binary = dist_binary.with_suffix(".exe")

    target = sidecar_dir / dist_binary.name
    if dist_binary.exists():
        shutil.copy2(dist_binary, target)
        print(f"Copied sidecar to: {target}")
    else:
        print(f"Warning: Could not find built binary at {dist_binary}")

    # Cleanup
    sidecar_entry.unlink(missing_ok=True)
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)
    Path(f"sidecar_main.spec").unlink(missing_ok=True)

    return True

def build_frontend():
    """Build the React frontend."""
    print("\n=== Building Frontend ===")

    # Install dependencies
    run_cmd(["npm", "install"], cwd=".")

    # Build with Vite
    run_cmd(["npm", "run", "build"], cwd=".")

    return True

def build_tauri():
    """Build the Tauri app."""
    print("\n=== Building Tauri App ===")

    # Check for Rust
    try:
        run_cmd(["cargo", "--version"], check=False)
    except:
        print("Rust not found. Please install from https://rustup.rs")
        return False

    # Install Tauri CLI
    run_cmd(["npm", "install", "-g", "@tauri-apps/cli"], check=False)

    # Build
    run_cmd(["npm", "run", "tauri:build"], cwd=".")

    return True

def main():
    print("AI Video Clipper - Desktop App Builder")
    print("=" * 40)

    platform_name = get_platform()
    print(f"Platform: {platform_name}")

    # Build steps
    steps = [
        ("Backend", build_backend),
        ("Frontend", build_frontend),
        ("Tauri", build_tauri),
    ]

    for name, func in steps:
        print(f"\n--- Building {name} ---")
        try:
            if not func():
                print(f"Failed to build {name}")
                sys.exit(1)
        except Exception as e:
            print(f"Error building {name}: {e}")
            sys.exit(1)

    print("\n" + "=" * 40)
    print("Build complete!")
    print("Find your app in: src-tauri/target/release/bundle/")

if __name__ == "__main__":
    main()