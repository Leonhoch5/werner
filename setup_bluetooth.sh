#!/bin/bash

echo "=== Bluetooth Setup for Windows Compatibility ==="

# Stop any conflicting services
sudo systemctl stop ModemManager 2>/dev/null
sudo killall bluetoothd 2>/dev/null

# Restart Bluetooth service
echo "Restarting Bluetooth service..."
sudo systemctl stop bluetooth
sleep 3
sudo systemctl start bluetooth
sleep 5

# Configure for maximum compatibility - no PIN required
echo "Configuring Bluetooth adapter for no-PIN pairing..."
sudo hciconfig hci0 down
sleep 1
sudo hciconfig hci0 up
sudo hciconfig hci0 piscan
sudo hciconfig hci0 sspmode 0  # Disable Secure Simple Pairing for easier connection
sudo hciconfig hci0 class 0x1F00

# Configure bluetoothctl for automatic pairing acceptance
echo "Setting up automatic pairing agent..."
timeout 2 sudo bluetoothctl <<EOF
power on
agent off
agent NoInputNoOutput
default-agent
discoverable on
pairable on
EOF

# Create a background pairing agent script that shows PIN
cat > /tmp/pair_agent.py << 'PYTHON_EOF'
#!/usr/bin/env python3
import subprocess
import time
import threading
import re

def monitor_bluetoothctl():
    """Monitor bluetoothctl output for pairing requests and PINs"""
    print("Starting Bluetooth pairing monitor...")
    
    proc = subprocess.Popen(['sudo', 'bluetoothctl'], 
                          stdin=subprocess.PIPE, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.STDOUT,
                          text=True, bufsize=1, universal_newlines=True)
    
    # Setup commands
    setup_commands = [
        'power on',
        'agent DisplayYesNo',
        'default-agent', 
        'discoverable on',
        'pairable on'
    ]
    
    for cmd in setup_commands:
        proc.stdin.write(cmd + '\n')
        proc.stdin.flush()
        time.sleep(0.5)
    
    print("=== PAIRING MONITOR ACTIVE ===")
    print("Watching for pairing requests...")
    print()
    
    try:
        while True:
            output = proc.stdout.readline()
            if output:
                line = output.strip()
                print(f"Bluetooth: {line}")
                
                # Look for pairing requests and PINs
                if "Request confirmation" in line:
                    print("\n" + "="*50)
                    print("🔵 PAIRING REQUEST DETECTED!")
                    print("="*50)
                
                if "Passkey:" in line or "PIN:" in line:
                    # Extract the PIN/passkey
                    pin_match = re.search(r'(\d{6})', line)
                    if pin_match:
                        pin = pin_match.group(1)
                        print("\n" + "="*50)
                        print(f"🔑 PIN CODE: {pin}")
                        print(f"🔑 ENTER THIS PIN ON WINDOWS: {pin}")
                        print("="*50)
                        print()
                
                if "Confirm passkey" in line:
                    print("\n" + "="*50) 
                    print("✅ CONFIRMING PAIRING REQUEST")
                    print("="*50)
                    proc.stdin.write('yes\n')
                    proc.stdin.flush()
                
                if "Request PIN code" in line:
                    print("\n" + "="*50)
                    print("🔑 SENDING DEFAULT PIN: 0000")
                    print("🔑 ENTER THIS PIN ON WINDOWS: 0000")
                    print("="*50)
                    proc.stdin.write('0000\n')
                    proc.stdin.flush()
                
                if "Pairing successful" in line:
                    print("\n" + "="*50)
                    print("✅ PAIRING SUCCESSFUL!")
                    print("="*50)
                    print()
                
                if "Failed to pair" in line:
                    print("\n" + "="*50)
                    print("❌ PAIRING FAILED!")
                    print("="*50)
                    print()
                    
    except KeyboardInterrupt:
        proc.terminate()
        print("Pairing monitor stopped")

if __name__ == "__main__":
    monitor_bluetoothctl()
PYTHON_EOF

# Start the pairing monitor in background
echo "Starting pairing monitor..."
python3 /tmp/pair_agent.py &
PAIR_PID=$!

echo ""
echo "=== Device Information ==="
hciconfig hci0
echo ""
echo "=== Ready for Windows Pairing ==="
echo "Device name: raspberrypiAR"
echo "MAC Address: B8:27:EB:B8:A9:10" 
echo "Pairing Agent PID: $PAIR_PID"
echo ""
echo "On Windows:"
echo "1. Go to Settings > Devices > Bluetooth & other devices"
echo "2. Click 'Add Bluetooth or other device'"
echo "3. Select 'Bluetooth'"
echo "4. Look for 'raspberrypiAR' in the list"
echo "5. Click it - WATCH THIS TERMINAL FOR THE PIN!"
echo ""
echo "🔑 THE PIN WILL BE DISPLAYED HERE WHEN PAIRING STARTS 🔑"
echo ""
echo "Device is discoverable. Pairing monitor running..."
echo "Monitor PID: $PAIR_PID"
echo ""
echo "When you start pairing from Windows, watch this terminal!"
echo "To stop the monitor: kill $PAIR_PID"