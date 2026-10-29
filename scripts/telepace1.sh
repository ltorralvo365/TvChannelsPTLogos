#!/bin/bash

yt-dlp -F "https://www.dailymotion.com/video/x9pha96" \
  | awk '!/^\[/ && /1080/ {print $1; exit}' \
  | xargs -I{} yt-dlp -f {} --get-url "https://www.dailymotion.com/video/x9pha96"
