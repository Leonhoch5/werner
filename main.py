import asyncio
import logging
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ESP32Controller:
    def __init__(self):
        self.client = None
        self.device = None
        self.connected = False
        
        # ESP32-C6 device info
        self.esp32_address = "AC:EB:E6:18:48:3A"
        self.esp32_name = "NimBLE_CONN"
        
        # These UUIDs will be discovered when we connect
        self.service_uuid = None
        self.characteristic_uuid = None
    
    async def scan_for_esp32(self, timeout=10):
        """Scan for ESP32 devices"""
        logger.info("Scanning for ESP32-C6 devices...")
        
        devices = await BleakScanner.discover(timeout=timeout)
        
        esp32_devices = []
        for device in devices:
            # Look for your specific ESP32 or any ESP32 device
            if (device.address == self.esp32_address or 
                (device.name and any(keyword in device.name.lower() 
                for keyword in ['nimble_conn', 'esp32', 'nimble']))):
                esp32_devices.append(device)
                logger.info(f"Found ESP32 device: {device.name} ({device.address})")
        
        if not esp32_devices:
            logger.warning("No ESP32 devices found. Showing all devices:")
            for device in devices:
                if device.name:
                    logger.info(f"Device: {device.name} ({device.address})")
        
        return esp32_devices
    
    async def connect_to_esp32(self, device_address=None, device_name=None):
        """Connect to ESP32 device by address or name"""
        
        # Use your specific ESP32 address if no other specified
        target_address = device_address or self.esp32_address
        
        try:
            logger.info(f"Connecting to {target_address}...")
            self.client = BleakClient(target_address)
            await self.client.connect()
            self.connected = True
            logger.info("Connected successfully!")
            
            # Discover services and find the first available characteristic
            await self.discover_services()
            
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            return False
    
    async def discover_services(self):
        """Discover available services and characteristics"""
        if not self.client or not self.connected:
            logger.error("Not connected to device")
            return
        
        logger.info("Discovering services...")
        services = self.client.services
        
        if not services:
            logger.error("No services found!")
            return
        
        # First, let's see ALL services and characteristics
        for service in services:
            logger.info(f"Service: {service.uuid} ({service.description})")
            
            for char in service.characteristics:
                logger.info(f"  Characteristic: {char.uuid} (Properties: {char.properties})")
        
        # Now find the best characteristic to use
        writable_chars = []
        readable_chars = []
        
        for service in services:
            # Skip generic Bluetooth services
            service_uuid_str = str(service.uuid).lower()
            if service_uuid_str.startswith('0000180') or service_uuid_str.startswith('0000181'):
                continue  # Skip generic services
                
            for char in service.characteristics:
                # Look for writable characteristics
                if 'write' in char.properties or 'write-without-response' in char.properties:
                    writable_chars.append((service.uuid, char.uuid, char.properties))
                    logger.info(f"Found writable characteristic: {char.uuid}")
                
                # Look for readable/notify characteristics  
                if 'read' in char.properties or 'notify' in char.properties:
                    readable_chars.append((service.uuid, char.uuid, char.properties))
                    logger.info(f"Found readable characteristic: {char.uuid}")
        
        # Set the first available writable characteristic
        if writable_chars:
            self.service_uuid = writable_chars[0][0]
            self.characteristic_uuid = writable_chars[0][1]
            logger.info(f"Using service: {self.service_uuid}")
            logger.info(f"Using characteristic: {self.characteristic_uuid}")
        elif readable_chars:
            self.service_uuid = readable_chars[0][0]
            self.characteristic_uuid = readable_chars[0][1]
            logger.info(f"Using readable service: {self.service_uuid}")
            logger.info(f"Using readable characteristic: {self.characteristic_uuid}")
        else:
            logger.error("No suitable characteristics found!")
            
        logger.info(f"Final characteristic UUID: {self.characteristic_uuid}")
    
    async def send_data(self, data, characteristic_uuid=None):
        """Send data to ESP32"""
        if not self.connected or not self.client:
            logger.error("Not connected to device")
            return False
        
        if not self.characteristic_uuid and not characteristic_uuid:
            logger.error("No characteristic UUID available for writing")
            return False
        
        try:
            char_uuid = characteristic_uuid or self.characteristic_uuid
            logger.info(f"Using characteristic UUID: {char_uuid}")
            
            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            await self.client.write_gatt_char(char_uuid, data)
            logger.info(f"Sent data: {data}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send data: {e}")
            logger.error(f"Characteristic UUID was: {char_uuid}")
            return False
    
    async def read_data(self, characteristic_uuid=None):
        """Read data from ESP32"""
        if not self.connected or not self.client:
            logger.error("Not connected to device")
            return None
        
        if not self.characteristic_uuid and not characteristic_uuid:
            logger.error("No characteristic UUID available for reading")
            return None
        
        try:
            char_uuid = characteristic_uuid or self.characteristic_uuid
            logger.info(f"Reading from characteristic UUID: {char_uuid}")
            
            data = await self.client.read_gatt_char(char_uuid)
            logger.info(f"Received data: {data}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to read data: {e}")
            logger.error(f"Characteristic UUID was: {char_uuid}")
            return None
    
    async def start_notifications(self, callback_func, characteristic_uuid=None):
        """Start receiving notifications from ESP32"""
        if not self.connected or not self.client:
            logger.error("Not connected to device")
            return False
        
        try:
            char_uuid = characteristic_uuid or self.characteristic_uuid
            await self.client.start_notify(char_uuid, callback_func)
            logger.info("Started notifications")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start notifications: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from ESP32"""
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from ESP32")

async def notification_handler(sender, data):
    """Handle notifications from ESP32"""
    logger.info(f"Notification from {sender}: {data}")

async def main():
    """Main function to connect and communicate with ESP32"""
    controller = ESP32Controller()
    
    try:
        # Connect to ESP32 (will auto-scan if no specific device given)
        success = await controller.connect_to_esp32()
        
        if success:
            # Start notifications if supported
            # await controller.start_notifications(notification_handler)
            
            # Example communication loop
            while controller.connected:
                try:
                    # Send a test message
                    await controller.send_data("Hello from Raspberry Pi!")
                    
                    # Wait a bit
                    await asyncio.sleep(2)
                    
                    # Read response (if ESP32 sends data)
                    response = await controller.read_data()
                    if response:
                        logger.info(f"ESP32 response: {response.decode('utf-8', errors='ignore')}")
                    
                    await asyncio.sleep(3)
                    
                except KeyboardInterrupt:
                    logger.info("Stopping...")
                    break
                except Exception as e:
                    logger.error(f"Communication error: {e}")
                    break
        
        else:
            logger.error("Failed to connect to ESP32")
    
    finally:
        await controller.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")