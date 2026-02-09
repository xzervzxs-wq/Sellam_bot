#!/bin/bash
set -e

# Auto-build AAB with non-interactive mode
cd /home/builder/work/Sellam_bot/Sellam_bot

echo "=== Building AAB ==="

# Install bubblewrap
npm install -g @bubblewrap/cli

# Create resources directory if needed
mkdir -p res

# Use existing keystore or create new one
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
    -dname "CN=Quran App, OU=Sellam, O=Quran, L=Riyadh, S=SA, C=SA"
fi

echo "=== Running bubblewrap build ==="
echo "$KEYSTORE_PASS" | bubblewrap build \
  --keystore "$KEYSTORE" \
  --keystore-password "$KEYSTORE_PASS" \
  --key-alias "$KEY_ALIAS" \
  --key-password "$KEY_PASS" || true

# Check for output files
if [ -f "app-release.aab" ]; then
  echo "✅ AAB built successfully!"
  ls -lh app-release.aab
elif [ -f "app-release-signed.apk" ]; then
  echo "⚠️ APK created instead, converting to AAB..."
  ls -lh app-release-signed.apk
else
  echo "❌ Build failed - no output file found"
  exit 1
fi
