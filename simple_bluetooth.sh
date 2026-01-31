#!/bin/bash

echo "=== Simple Interactive Bluetooth Setup ==="
echo "This will run bluetoothctl interactively so you can see all output"
echo ""

# Basic setup
sudo hciconfig hci0 up
sudo hciconfig hci0 piscan
sudo hciconfig hci0 sspmode 1

echo "Device info:"
hciconfig hci0
echo ""
echo "Starting bluetoothctl - you'll see all pairing activity here"
echo "When Windows tries to pair, you'll see the PIN in this terminal!"
echo ""
echo "Commands you can use:"
echo "  power on"
echo "  agent on"  
echo "  default-agent"
echo "  discoverable on"
echo "  pairable on"
echo "  yes        (to accept pairing)"
echo "  quit       (to exit)"
echo ""

# Run bluetoothctl interactively
sudo bluetoothctl