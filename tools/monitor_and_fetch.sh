#!/bin/bash
# Monitor server and auto-fetch when back online, then commit the real images

MAX_WAIT=3600  # 1 hour max
POLL_INTERVAL=30
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
  if python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
try:
  s.connect(('104.225.128.45', 443))
  exit(0)
except:
  exit(1)
" 2>/dev/null; then
    echo "[$(date)] Server is up! Starting download..."
    python3 tools/fetch_real_images.py
    
    # Check if anything was actually downloaded
    if [ -s tools/placeholder-manifest.txt ]; then
      REMAINING=$(wc -l < tools/placeholder-manifest.txt)
      echo "[$(date)] Download complete. $REMAINING placeholder(s) still remain."
      
      if [ $REMAINING -eq 0 ]; then
        echo "[$(date)] All images replaced! Committing..."
        git add assets/images tools/placeholder-manifest.txt
        git commit -m "Replace placeholder images with real photos from original site

All 443 placeholder images have been successfully downloaded and replaced.
Site now includes complete original photography.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
        echo "[$(date)] Commit complete!"
      fi
    fi
    exit 0
  fi
  
  echo "[$(date)] Server still down. Waiting ${POLL_INTERVAL}s... (${ELAPSED}/${MAX_WAIT})"
  sleep $POLL_INTERVAL
  ELAPSED=$((ELAPSED + POLL_INTERVAL))
done

echo "[$(date)] Max wait time exceeded. Server did not recover."
exit 1
