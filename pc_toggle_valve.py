import asyncio

from bleak import BleakClient, BleakScanner


DEVICE_NAME = "ESP32C3_VALVE_CTRL"
SERVICE_UUID = "7b7d0001-2f4a-4f3d-9b4a-6a9d7f3c1000"
COMMAND_CHAR_UUID = "7b7d0002-2f4a-4f3d-9b4a-6a9d7f3c1000"
STATE_CHAR_UUID = "7b7d0003-2f4a-4f3d-9b4a-6a9d7f3c1000"


async def main():
    print(f"Scanning for {DEVICE_NAME}...")
    device = await BleakScanner.find_device_by_filter(
        lambda dev, adv: dev.name == DEVICE_NAME
        or (adv.local_name == DEVICE_NAME if adv else False),
        timeout=10.0,
    )

    if device is None:
        raise RuntimeError(f"BLE device not found: {DEVICE_NAME}")

    async with BleakClient(device) as client:
        print(f"Connected: {device.address}")

        await client.write_gatt_char(COMMAND_CHAR_UUID, b"TOGGLE", response=True)

        state_bytes = await client.read_gatt_char(STATE_CHAR_UUID)
        state = state_bytes.decode("utf-8")
        print(f"GPIO10 state: {state}")


if __name__ == "__main__":
    asyncio.run(main())
