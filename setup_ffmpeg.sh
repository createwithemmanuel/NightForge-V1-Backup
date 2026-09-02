#!/usr/bin/env bash
set -e
if command -v ffmpeg >/dev/null 2>&1; then
  echo "FFmpeg already available."
  exit 0
fi
echo "Installing FFmpeg..."
apt-get update -y
apt-get install -y ffmpeg
ffmpeg -version | head -n 1
