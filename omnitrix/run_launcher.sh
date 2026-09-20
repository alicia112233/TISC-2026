#!/bin/bash
# Run launcher with automatic credentials and keep it running
# Then when port is ready, run the exploit

export LYLA_USERNAME=aliciatangweishan@gmail.com
export LYLA_PASSWORD=Aliciatang33!
export LYLA_LOCAL_PORT=7878

echo "[*] Starting Omnitrix challenge connector..."
cd ~/omnitrix-connector

# Start the launcher in background
./launcher.sh > /tmp/omnitrix_launcher.log 2>&1 &
LAUNCHER_PID=$!
echo "[*] Launcher PID: $LAUNCHER_PID"

# Wait for port to open
echo "[*] Waiting for port 7878 to be available..."
for i in $(seq 1 60); do
    if ss -tlnp 2>/dev/null | grep -q ':7878'; then
        echo "[+] Port 7878 is open! Launcher is forwarding."
        cat /tmp/omnitrix_launcher.log
        echo ""
        echo "[*] Running exploit..."
        python3 /tmp/exploit.py
        break
    fi
    sleep 2
    echo -n "."
done

echo ""
echo "[*] Launcher log:"
cat /tmp/omnitrix_launcher.log

# Keep launcher alive
wait $LAUNCHER_PID
