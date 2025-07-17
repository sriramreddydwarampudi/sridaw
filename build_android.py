#!/usr/bin/env python3
"""
Android build script for SriDAW
This script handles the build process and provides detailed logging
"""

import subprocess
import sys
import os
import time

def run_command(cmd, description=""):
    """Run a command and capture output"""
    print(f"\n{'='*60}")
    print(f"Running: {description or cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=3600  # 1 hour timeout
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print("Command timed out!")
        return False, "", "Timeout"
    except Exception as e:
        print(f"Command failed: {e}")
        return False, "", str(e)

def check_prerequisites():
    """Check if build prerequisites are met"""
    print("Checking prerequisites...")
    
    # Check Python
    success, stdout, stderr = run_command("python3 --version", "Check Python version")
    if not success:
        print("❌ Python3 not found")
        return False
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ main.py not found - are you in the right directory?")
        return False
    
    if not os.path.exists("buildozer.spec"):
        print("❌ buildozer.spec not found")
        return False
    
    print("✅ Prerequisites check passed")
    return True

def install_buildozer():
    """Install buildozer if not available"""
    print("Installing buildozer...")
    
    success, stdout, stderr = run_command(
        "python3 -m pip install --user buildozer", 
        "Install buildozer"
    )
    
    if success:
        # Add to PATH
        home = os.path.expanduser("~")
        local_bin = os.path.join(home, ".local", "bin")
        current_path = os.environ.get("PATH", "")
        if local_bin not in current_path:
            os.environ["PATH"] = f"{current_path}:{local_bin}"
        
        print("✅ Buildozer installed")
        return True
    else:
        print("❌ Failed to install buildozer")
        return False

def clean_build():
    """Clean previous build artifacts"""
    print("Cleaning previous builds...")
    
    dirs_to_clean = [".buildozer", "bin"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            success, stdout, stderr = run_command(f"rm -rf {dir_name}", f"Remove {dir_name}")
            if success:
                print(f"✅ Cleaned {dir_name}")
            else:
                print(f"⚠️ Could not clean {dir_name}")

def build_apk():
    """Build the APK"""
    print("Building APK...")
    
    # Set environment variables for Android build
    env_vars = {
        "ANDROID_HOME": os.path.expanduser("~/.buildozer/android/platform/android-sdk"),
        "ANDROID_SDK_ROOT": os.path.expanduser("~/.buildozer/android/platform/android-sdk"),
        "PATH": os.environ.get("PATH", "")
    }
    
    # Update environment
    for key, value in env_vars.items():
        os.environ[key] = value
    
    success, stdout, stderr = run_command(
        "buildozer android debug", 
        "Build APK with buildozer"
    )
    
    if success:
        print("✅ APK build completed successfully!")
        
        # Find the APK file
        bin_dir = "bin"
        if os.path.exists(bin_dir):
            apk_files = [f for f in os.listdir(bin_dir) if f.endswith('.apk')]
            if apk_files:
                apk_path = os.path.join(bin_dir, apk_files[0])
                print(f"📱 APK created: {apk_path}")
                
                # Show file size
                size = os.path.getsize(apk_path)
                print(f"📏 APK size: {size / (1024*1024):.1f} MB")
                
                return True, apk_path
        
        print("⚠️ APK file not found in bin directory")
        return True, None
    else:
        print("❌ APK build failed")
        return False, None

def main():
    """Main build process"""
    print("SriDAW Android Build Script")
    print("=" * 60)
    
    start_time = time.time()
    
    # Check prerequisites
    if not check_prerequisites():
        return 1
    
    # Install buildozer if needed
    success, stdout, stderr = run_command("which buildozer", "Check buildozer")
    if not success:
        if not install_buildozer():
            return 1
    
    # Clean previous builds
    clean_build()
    
    # Build APK
    success, apk_path = build_apk()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("BUILD SUMMARY")
    print("=" * 60)
    print(f"Duration: {duration/60:.1f} minutes")
    
    if success:
        print("✅ Build completed successfully!")
        if apk_path:
            print(f"📱 APK: {apk_path}")
            print("\nTo install on device:")
            print(f"  adb install {apk_path}")
        return 0
    else:
        print("❌ Build failed!")
        print("\nCheck the logs above for error details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())