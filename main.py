import bluetooth
import threading
import time
import subprocess

class BluetoothServer:
    def __init__(self):
        self.server_socket = None
        self.running = False
    
    def make_discoverable(self):
        """Make the device discoverable"""
        try:
            # Make device discoverable
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'piscan'], check=True)
            print("Device is now discoverable")
        except subprocess.CalledProcessError:
            print("Failed to make device discoverable")
    
    def start_server(self):
        """Start Bluetooth RFCOMM server"""
        self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        port = bluetooth.PORT_ANY
        
        self.server_socket.bind(("", port))
        self.server_socket.listen(1)
        
        port = self.server_socket.getsockname()[1]
        
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
        
        print(f"Waiting for connection on RFCOMM channel {port}")
        print(f"Connect to this device using MAC address and channel {port}")
        self.running = True
        
        while self.running:
            try:
                client_socket, client_info = self.server_socket.accept()
                print(f"Accepted connection from {client_info}")j
                
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket,)
                )
                client_thread.start()
                
            except bluetooth.BluetoothError as e:
                if self.running:
                    print(f"Bluetooth error: {e}")
                break
    
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
    bt_server = BluetoothServer()
    
    try:
        bt_server.make_discoverable()
        bt_server.start_server()
    except KeyboardInterrupt:
        print("\nShutting down...")
        bt_server.stop()