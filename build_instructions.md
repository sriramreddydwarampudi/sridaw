# Building SriDAW Android APK

## Prerequisites
You need a Linux system (Ubuntu/Debian recommended) or WSL on Windows with:

```bash
# Install system dependencies
sudo apt update
sudo apt install -y git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# Install buildozer
pip3 install --user buildozer

# Add to PATH if needed
export PATH=$PATH:~/.local/bin
```

## Build Steps

1. Clone or download this project
2. Navigate to the project directory
3. Clean any previous builds:
   ```bash
   rm -rf .buildozer
   ```
4. Build the APK:
   ```bash
   buildozer android debug
   ```

## First Build
The first build will take a long time (30-60 minutes) as it downloads:
- Android SDK
- Android NDK  
- Python-for-android
- All dependencies

## Output
The APK will be created in: `bin/sridaw-1.0-arm64-v8a-debug.apk`

## Troubleshooting

### If build fails:
1. Check buildozer logs in `.buildozer/`
2. Try cleaning: `buildozer android clean`
3. Update buildozer: `pip3 install --upgrade buildozer`

### Common issues:
- Java version conflicts: Use OpenJDK 8
- Missing system packages: Install build-essential
- Permission issues: Don't run as root

### Android permissions:
The app requests:
- WRITE_EXTERNAL_STORAGE (for saving files)
- READ_EXTERNAL_STORAGE (for loading files)
- INTERNET (for potential future features)

## Testing
Install the APK on Android device:
```bash
adb install bin/sridaw-1.0-arm64-v8a-debug.apk
```

Or transfer the APK file to your device and install manually.