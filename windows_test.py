import serial
import serial.tools.list_ports
import time

def find_bluetooth_ports():
    """Find available Bluetooth COM ports"""
    ports = serial.tools.list_ports.comports()
    bluetooth_ports = []
    
    for port in ports:
        if 'bluetooth' in port.description.lower() or 'rfcomm' in port.description.lower():
            bluetooth_ports.append(port)
    
    return bluetooth_ports

def test_connection():
    print("Looking for Bluetooth COM ports...")
    bluetooth_ports = find_bluetooth_ports()
    
    if not bluetooth_ports:
        print("No Bluetooth COM ports found.")
        print("Make sure the device is paired and the 'Serial Port' service is enabled.")
        return
    
    for port in bluetooth_ports:
        print(f"Found: {port.device} - {port.description}")
        
        try:
            print(f"Trying to connect to {port.device}...")
            ser = serial.Serial(port.device, 9600, timeout=2)
            
            # Send test message
            test_msg = "Hello from Windows!\r\n"
            ser.write(test_msg.encode('utf-8'))
            print(f"Sent: {test_msg.strip()}")
            
            # Wait for response
            time.sleep(1)
            response = ser.read(100)
            if response:
                print(f"Received: {response.decode('utf-8', errors='ignore')}")
            else:
                print("No response received")
            
            ser.close()
            print("Connection test successful!")
            break
            
        except serial.SerialException as e:
            print(f"Failed to connect to {port.device}: {e}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
