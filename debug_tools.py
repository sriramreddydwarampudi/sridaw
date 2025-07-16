#!/usr/bin/env python3
"""
Debug tools for SriDAW Android development
"""

import subprocess
import sys
import time
import threading
import os

class ADBLogger:
    def __init__(self):
        self.process = None
        self.running = False
        
    def check_adb(self):
        """Check if ADB is available"""
        try:
            result = subprocess.run(['adb', 'version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def check_device(self):
        """Check if device is connected"""
        try:
            result = subprocess.run(['adb', 'devices'], 
                                  capture_output=True, text=True, timeout=5)
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            devices = [line for line in lines if line.strip() and 'device' in line]
            return len(devices) > 0
        except:
            return False
    
    def start_logging(self, filter_tag="SriDAW", save_to_file=True):
        """Start ADB logcat with filtering"""
        if not self.check_adb():
            print("❌ ADB not found. Please install Android SDK platform-tools")
            return False
            
        if not self.check_device():
            print("❌ No Android device connected")
            print("   Make sure USB debugging is enabled and device is connected")
            return False
        
        print(f"🔍 Starting ADB logcat for {filter_tag}...")
        print("   Press Ctrl+C to stop logging")
        
        # Clear existing logs
        subprocess.run(['adb', 'logcat', '-c'], capture_output=True)
        
        # Prepare log file
        log_file = None
        if save_to_file:
            log_filename = f"sridaw_debug_{int(time.time())}.log"
            log_file = open(log_filename, 'w')
            print(f"📝 Saving logs to: {log_filename}")
        
        try:
            # Start logcat process
            cmd = ['adb', 'logcat', '-s', f'{filter_tag}:*', 'AndroidRuntime:E', 'System.err:W']
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE, text=True, bufsize=1)
            self.running = True
            
            print("📱 Logs will appear below (install and run the app now):")
            print("-" * 60)
            
            # Read and display logs
            for line in iter(self.process.stdout.readline, ''):
                if not self.running:
                    break
                    
                timestamp = time.strftime("%H:%M:%S")
                formatted_line = f"[{timestamp}] {line.rstrip()}"
                
                # Color coding for different log levels
                if "ERROR" in line or "FATAL" in line:
                    print(f"🔴 {formatted_line}")
                elif "WARN" in line:
                    print(f"🟡 {formatted_line}")
                elif "INFO" in line:
                    print(f"🔵 {formatted_line}")
                else:
                    print(f"⚪ {formatted_line}")
                
                if log_file:
                    log_file.write(formatted_line + '\n')
                    log_file.flush()
                    
        except KeyboardInterrupt:
            print("\n⏹️  Logging stopped by user")
        except Exception as e:
            print(f"❌ Logging error: {e}")
        finally:
            self.stop_logging()
            if log_file:
                log_file.close()
                print(f"📁 Log saved to: {log_filename}")
    
    def stop_logging(self):
        """Stop ADB logging"""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process = None

def install_apk(apk_path):
    """Install APK to connected device"""
    logger = ADBLogger()
    
    if not logger.check_adb():
        print("❌ ADB not found")
        return False
        
    if not logger.check_device():
        print("❌ No device connected")
        return False
    
    if not os.path.exists(apk_path):
        print(f"❌ APK not found: {apk_path}")
        return False
    
    print(f"📦 Installing APK: {apk_path}")
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
    """Launch the SriDAW app"""
    try:
        subprocess.run(['adb', 'shell', 'am', 'start', '-n', 
                       'org.example.sridaw/org.kivy.android.PythonActivity'], 
                      timeout=10)
        print("🚀 App launched")
    except Exception as e:
        print(f"❌ Launch error: {e}")

def main():
    if len(sys.argv) < 2:
        print("SriDAW Debug Tools")
        print("Usage:")
        print("  python debug_tools.py log          - Start ADB logging")
        print("  python debug_tools.py install <apk> - Install APK")
        print("  python debug_tools.py launch       - Launch app")
        print("  python debug_tools.py full <apk>   - Install, launch, and log")
        return
    
    command = sys.argv[1]
    
    if command == "log":
        logger = ADBLogger()
        logger.start_logging()
        
    elif command == "install" and len(sys.argv) > 2:
        install_apk(sys.argv[2])
        
    elif command == "launch":
        launch_app()
        
    elif command == "full" and len(sys.argv) > 2:
        apk_path = sys.argv[2]
        if install_apk(apk_path):
            print("⏳ Waiting 3 seconds before launch...")
            time.sleep(3)
            launch_app()
            print("⏳ Waiting 2 seconds before logging...")
            time.sleep(2)
            logger = ADBLogger()
            logger.start_logging()
    else:
        print("❌ Invalid command")

if __name__ == "__main__":
    main()