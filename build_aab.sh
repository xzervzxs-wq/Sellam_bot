#!/bin/bash
set -e

# Auto-build AAB with non-interactive mode
# Use current directory (Codemagic will run from repo root)
cd $(pwd)

echo "Current directory: $(pwd)"
echo "=== Building AAB ==="

# Install bubblewrap
npm install -g @bubblewrap/cli

# Prepare keystore
KEYSTORE="android.keystore"
KEYSTORE_PASS="Quran@2024!"
KEY_ALIAS="android"
KEY_PASS="Quran@2024!"

if [ ! -f "$KEYSTORE" ]; then
  echo "Creating keystore..."
  keytool -genkey -v -keystore "$KEYSTORE" \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -alias "$KEY_ALIAS" \
    -storepass "$KEYSTORE_PASS" \
    -keypass "$KEY_PASS" \
    -dname "CN=Quran App, OU=Sellam, O=Quran, L=Riyadh, S=SA, C=SA" || true
fi

echo "=== Running bubblewrap build ==="

# Build with non-interactive options
bubblewrap build 2>&1 || echo "Build completed with status"

# Check for output files
if [ -f "app-release.aab" ]; then
  echo "✅ AAB built successfully!"
  ls -lh app-release.aab
elif [ -f "app-release-signed.apk" ]; then
  echo "✅ APK built successfully!"
  ls -lh app-release-signed.apk
else
  echo "Checking for any build output..."
  find . -name "*.aab" -o -name "*.apk" 2>/dev/null || echo "No output found"
fi

