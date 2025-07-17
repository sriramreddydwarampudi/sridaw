#!/usr/bin/env python3
"""
SriDAW Build Troubleshooting Script
"""

import os
import sys
import subprocess
import platform

def check_command(cmd, description):
    """Check if a command exists and works"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}: OK")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description}: FAILED")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description}: ERROR - {e}")
        return False

def check_file(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: Found")
        return True
    else:
        print(f"❌ {description}: Missing")
        return False

def main():
    print("SriDAW Build Troubleshooting")
    print("=" * 50)
    
    # System info
    print(f"Platform: {platform.platform()}")
    print(f"Python: {sys.version}")
    print()
    
    # Check basic commands
    print("Checking basic commands:")
    check_command("python3 --version", "Python3")
    check_command("pip3 --version", "pip3")
    check_command("java -version", "Java")
    check_command("git --version", "Git")
    print()
    
    # Check project files
    print("Checking project files:")
    check_file("main.py", "Main application")
    check_file("buildozer.spec", "Buildozer config")
    check_file("music21/__init__.py", "Music21 module")
    print()
    
    # Check buildozer
    print("Checking buildozer:")
    if check_command("buildozer --version", "Buildozer"):
        print("   Buildozer is installed")
    else:
        print("   Installing buildozer...")
        if check_command("python3 -m pip install --user buildozer", "Install buildozer"):
            # Add to PATH
            home = os.path.expanduser("~")
            local_bin = os.path.join(home, ".local", "bin")
            current_path = os.environ.get("PATH", "")
            if local_bin not in current_path:
                os.environ["PATH"] = f"{current_path}:{local_bin}"
            check_command("buildozer --version", "Buildozer after install")
    print()
    
    # Check Android SDK/NDK
    print("Checking Android environment:")
    buildozer_dir = os.path.expanduser("~/.buildozer")
    if os.path.exists(buildozer_dir):
        print(f"✅ Buildozer directory exists: {buildozer_dir}")
        android_dir = os.path.join(buildozer_dir, "android")
        if os.path.exists(android_dir):
            print(f"✅ Android directory exists: {android_dir}")
        else:
            print(f"❌ Android directory missing: {android_dir}")
    else:
        print(f"❌ Buildozer directory missing: {buildozer_dir}")
    print()
    
    # Recommendations
    print("Recommendations:")
    print("1. If Java is missing: sudo apt install openjdk-8-jdk")
    print("2. If build fails: rm -rf .buildozer && buildozer android debug")
    print("3. For first build: Expect 30-60 minutes download time")
    print("4. Check logs in .buildozer/android/platform/build-*/build.log")

if __name__ == "__main__":
    main()