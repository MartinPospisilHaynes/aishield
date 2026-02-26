#!/bin/bash
# Monitor gen11 progress and download results when done
# Usage: ./monitor_gen11.sh

VPS="root@46.28.110.102"
LOCAL_DIR="/Users/martinhaynes/Projects/aishield/docs_gen11"
REMOTE_LOG="/opt/aishield/gen11.log"
REMOTE_RESULT="/opt/aishield/gen11_result.json"

mkdir -p "$LOCAL_DIR"

echo "=== Monitoring gen11 progress ==="
echo "Local output: $LOCAL_DIR"
echo ""

LAST_DOC=0

while true; do
    # Check if process is still running
    RUNNING=$(ssh "$VPS" "ps aux | grep gen11.py | grep -v grep | wc -l" 2>/dev/null)
    
    # Get latest completed doc count
    CURRENT_DOC=$(ssh "$VPS" "grep -c 'DOKUMENT.*HOTOV' $REMOTE_LOG 2>/dev/null" 2>/dev/null)
    
    if [ "$CURRENT_DOC" -gt "$LAST_DOC" ] 2>/dev/null; then
        # New doc(s) completed — show details
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ssh "$VPS" "grep 'DOKUMENT.*HOTOV\|Skóre:' $REMOTE_LOG" 2>/dev/null | tail -$(( (CURRENT_DOC - LAST_DOC) * 2 ))
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        LAST_DOC=$CURRENT_DOC
    fi
    
    # Show latest activity
    LATEST=$(ssh "$VPS" "tail -1 $REMOTE_LOG 2>/dev/null" 2>/dev/null)
    printf "\r[%s] Docs: %s/11 | %s" "$(date +%H:%M:%S)" "$CURRENT_DOC" "$(echo "$LATEST" | sed 's/.*\] //' | cut -c1-60)"
    
    # Check if gen11 finished
    if [ "$RUNNING" = "0" ] || [ "$RUNNING" = "" ]; then
        echo ""
        echo ""
        echo "=== gen11 FINISHED! ==="
        
        # Download result JSON
        scp "$VPS:$REMOTE_RESULT" "$LOCAL_DIR/gen11_result.json" 2>/dev/null
        
        if [ -f "$LOCAL_DIR/gen11_result.json" ]; then
            echo "Result JSON downloaded."
            
            # Extract PDF URLs and download them
            echo "Downloading PDFs from Supabase..."
            python3 -c "
import json, urllib.request, os
with open('$LOCAL_DIR/gen11_result.json') as f:
    data = json.load(f)
for doc in data.get('documents', []):
    url = doc.get('download_url', '')
    fname = doc.get('filename', '')
    if url and fname:
        print(f'  Downloading: {fname}')
        try:
            urllib.request.urlretrieve(url, os.path.join('$LOCAL_DIR', fname))
            print(f'  ✓ {fname}')
        except Exception as e:
            print(f'  ✗ {fname}: {e}')
print('Done!')
"
        fi
        
        # Also download the full log
        scp "$VPS:$REMOTE_LOG" "$LOCAL_DIR/gen11.log" 2>/dev/null
        echo "Log downloaded."
        
        echo ""
        echo "=== All files in $LOCAL_DIR ==="
        ls -la "$LOCAL_DIR"
        break
    fi
    
    sleep 30
done
