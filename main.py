import bluetooth
import threading
import time
import subprocess
import os

class BluetoothServer:
    def __init__(self):
        self.server_socket = None
        self.running = False
    
    def make_discoverable(self):
        """Make the device discoverable"""
        try:
            # Make device discoverable and connectable
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'up'], check=True)
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'piscan'], check=True)
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'sspmode', '1'], check=True)
            print("Device is now discoverable")
            
            # Show MAC address
            result = subprocess.run(['hciconfig', 'hci0'], capture_output=True, text=True)
            print("Bluetooth adapter info:")
            print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to make device discoverable: {e}")
    
    def start_server(self):
        """Start Bluetooth RFCOMM server"""
        try:
            self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            
            # Use ANY port for better compatibility with Windows
            port = bluetooth.PORT_ANY
            
            self.server_socket.bind(("", port))
            self.server_socket.listen(1)
            
            actual_port = self.server_socket.getsockname()[1]
            
            try:
                bluetooth.advertise_service(
                    self.server_socket, "RaspberryPiService",
                    service_id="1e0ca4ea-299d-4335-93eb-27fcfe7fa848",
                    service_classes=[bluetooth.SERIAL_PORT_CLASS],
                    profiles=[bluetooth.SERIAL_PORT_PROFILE]
                )
                print("Service advertised successfully")
            except bluetooth.BluetoothError as e:
                print(f"Warning: Could not advertise service: {e}")
                print("Service will still work for direct connections")
            
            print(f"Server started on RFCOMM channel {actual_port}")
            print(f"Device MAC address: B8:27:EB:B8:A9:10")
            print("From your phone:")
            print("1. Pair with this device in Bluetooth settings")
            print("2. Use a Bluetooth terminal app (like 'Serial Bluetooth Terminal')")
            print("3. Connect to the paired device")
            print("Waiting for connections...")
            
            self.running = True
            
            while self.running:
                try:
                    client_socket, client_info = self.server_socket.accept()
                    print(f"Connection accepted from {client_info}")
                    
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except bluetooth.BluetoothError as e:
                    if self.running:
                        print(f"Bluetooth error: {e}")
                    break
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    break
        
        except Exception as e:
            print(f"Failed to start server: {e}")
            print("Make sure you have the necessary permissions (try with sudo)")
            print("And that no other Bluetooth service is using the port")
    
    def handle_client(self, client_socket):
        """Handle connected client"""
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                message = data.decode('utf-8')
                print(f"Received: {message}")
                
                # Echo back
                client_socket.send(f"Echo: {message}".encode('utf-8'))
                
        except bluetooth.BluetoothError as e:
            print(f"Client error: {e}")
        finally:
            client_socket.close()
            print("Client disconnected")
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

if __name__ == "__main__":
    # Check if running as root
    if os.geteuid() != 0:
        print("Note: Some Bluetooth operations may require sudo")
    
    bt_server = BluetoothServer()
    
    try:
        bt_server.make_discoverable()
        bt_server.start_server()
    except KeyboardInterrupt:
        print("\nShutting down...")
        bt_server.stop()