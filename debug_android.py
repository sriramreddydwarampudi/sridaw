#!/usr/bin/env python3
"""
Android debugging script for SriDAW
"""

import subprocess
import sys
import time
import os

def check_adb():
    """Check if ADB is available"""
    try:
        result = subprocess.run(['adb', 'version'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def check_device():
    """Check if device is connected"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().split('\n')[1:]
        devices = [line for line in lines if line.strip() and 'device' in line]
        return len(devices) > 0
    except:
        return False

def install_apk():
    """Install the APK"""
    apk_files = []
    if os.path.exists('bin'):
        apk_files = [f for f in os.listdir('bin') if f.endswith('.apk')]
    
    if not apk_files:
        print("❌ No APK found in bin/ directory")
        return False
    
    apk_path = os.path.join('bin', apk_files[0])
    print(f"📦 Installing {apk_path}...")
    
    try:
        result = subprocess.run(['adb', 'install', '-r', apk_path], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ APK installed successfully")
            return True
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def launch_app():
    """Launch the app"""
    try:
        subprocess.run(['adb', 'shell', 'am', 'start', '-n', 
                       'org.example.sridaw/org.kivy.android.PythonActivity'], 
                      timeout=10)
        print("🚀 App launched")
        return True
    except Exception as e:
        print(f"❌ Launch error: {e}")
        return False

def start_logging():
    """Start ADB logging"""
    print("🔍 Starting ADB logcat...")
    print("   Press Ctrl+C to stop")
    print("-" * 50)
    
    # Clear existing logs
    subprocess.run(['adb', 'logcat', '-c'], capture_output=True)
    
    try:
        # Start logcat with filtering
        cmd = ['adb', 'logcat', '-s', 'python:*', 'SriDAW:*', 'AndroidRuntime:E']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, bufsize=1)
        
        for line in iter(process.stdout.readline, ''):
            timestamp = time.strftime("%H:%M:%S")
            formatted_line = f"[{timestamp}] {line.rstrip()}"
            
            if "ERROR" in line or "FATAL" in line:
                print(f"🔴 {formatted_line}")
            elif "WARN" in line:
                print(f"🟡 {formatted_line}")
            else:
                print(f"⚪ {formatted_line}")
                
    except KeyboardInterrupt:
        print("\n⏹️  Logging stopped")
    except Exception as e:
        print(f"❌ Logging error: {e}")

def main():
    print("SriDAW Android Debug Tool")
    print("=" * 40)
    
    if not check_adb():
        print("❌ ADB not found. Install Android SDK platform-tools")
        return 1
    
    if not check_device():
        print("❌ No Android device connected")
        print("   Enable USB debugging and connect device")
        return 1
    
    print("✅ ADB and device ready")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "install":
            install_apk()
        elif command == "launch":
            launch_app()
        elif command == "log":
            start_logging()
        elif command == "full":
            if install_apk():
                time.sleep(2)
                launch_app()
                time.sleep(3)
                start_logging()
    else:
        print("Usage:")
        print("  python debug_android.py install  - Install APK")
        print("  python debug_android.py launch   - Launch app")
        print("  python debug_android.py log      - Start logging")
        print("  python debug_android.py full     - Install, launch, and log")

if __name__ == "__main__":
    main()