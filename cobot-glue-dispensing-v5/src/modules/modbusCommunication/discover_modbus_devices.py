# modbus_discovery.py

from modules.modbusCommunication.ModbusClient import ModbusClient
from modules.modbusCommunication.ModbusController import ModbusController
import minimalmodbus


def discover_modbus_devices(
    start_addr: int = 1,
    end_addr: int = 247,
    test_register: int = 0,
    decimals: int = 0
):
    """
    Scan the Modbus RTU bus for active slave devices.

    Args:
        start_addr (int): First slave address to scan.
        end_addr (int): Last slave address to scan.
        test_register (int): A harmless register to read to check presence.
        decimals (int): Number of decimals to pass to read_register().

    Returns:
        list[int]: List of detected slave IDs.
    """
    found = []

    print(f"🔍 Starting Modbus RTU discovery from {start_addr} to {end_addr} ...")

    for slave_id in range(start_addr, end_addr + 1):
        client: ModbusClient = ModbusController.getModbusClient(slave_id)

        try:
            # Try reading a simple register
            client.read_register(test_register, decimals)
            print(f"✔️ Device detected at address {slave_id}")
            found.append(slave_id)

        except minimalmodbus.NoResponseError:
            pass  # No device responds here

        except IOError:
            pass  # CRC or bus error → assume no device

        except Exception as e:
            print(f"⚠️ Unexpected error at {slave_id}: {e}")

    print(f"\n🎉 Discovery complete. Found devices: {found}")
    return found


if __name__ == "__main__":
    discover_modbus_devices()
