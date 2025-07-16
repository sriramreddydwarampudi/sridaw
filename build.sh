#!/bin/bash

# SriDAW Android Build Script
# Run this on a Linux system with buildozer installed

set -e  # Exit on any error

echo "🚀 Starting SriDAW Android build..."

# Check if buildozer is installed
if ! command -v buildozer &> /dev/null; then
    echo "❌ Buildozer not found. Please install it first:"
    echo "   pip3 install --user buildozer"
    echo "   export PATH=\$PATH:~/.local/bin"
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf .buildozer bin

# Create bin directory
mkdir -p bin

# Build the APK
echo "🔨 Building APK (this may take a while on first build)..."
buildozer android debug

# Check if build was successful
if [ -f "bin/sridaw-1.0-arm64-v8a-debug.apk" ]; then
    echo "✅ Build successful!"
    echo "📱 APK created: bin/sridaw-1.0-arm64-v8a-debug.apk"
    echo "📊 APK size: $(du -h bin/sridaw-1.0-arm64-v8a-debug.apk | cut -f1)"
else
    echo "❌ Build failed. Check the logs above."
    exit 1
fi

echo "🎉 Done! You can now install the APK on your Android device."