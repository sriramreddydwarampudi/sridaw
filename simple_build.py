#!/usr/bin/env python3
"""
Simplified Android build script for SriDAW
"""

import subprocess
import sys
import os
import time

def run_cmd(cmd, description=""):
    """Run command with output"""
    print(f"\n{'='*50}")
    print(f"Running: {description or cmd}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"Return code: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("SriDAW Simple Build Script")
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ main.py not found - wrong directory?")
        return 1
    
    # Install buildozer
    print("Installing buildozer...")
    if not run_cmd("python3 -m pip install --user buildozer", "Install buildozer"):
        print("❌ Failed to install buildozer")
        return 1
    
    # Add to PATH
    home = os.path.expanduser("~")
    local_bin = os.path.join(home, ".local", "bin")
    current_path = os.environ.get("PATH", "")
    if local_bin not in current_path:
        os.environ["PATH"] = f"{current_path}:{local_bin}"
    
    # Clean previous builds
    print("Cleaning previous builds...")
    run_cmd("rm -rf .buildozer bin", "Clean builds")
    
    # Initialize buildozer (this will download Android SDK/NDK)
    print("Initializing buildozer...")
    if not run_cmd("buildozer android debug", "Build APK"):
        print("❌ Build failed")
        return 1
    
    # Check for APK
    if os.path.exists("bin") and any(f.endswith('.apk') for f in os.listdir("bin")):
        apk_files = [f for f in os.listdir("bin") if f.endswith('.apk')]
        apk_path = os.path.join("bin", apk_files[0])
        size = os.path.getsize(apk_path) / (1024*1024)
        print(f"✅ APK created: {apk_path} ({size:.1f} MB)")
        return 0
    else:
        print("❌ APK not found")
        return 1

if __name__ == "__main__":
    sys.exit(main())