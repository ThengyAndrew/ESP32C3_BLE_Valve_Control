import asyncio
import threading
import tkinter as tk
from tkinter import messagebox

from bleak import BleakClient, BleakScanner


DEVICE_NAME = "ESP32C3_VALVE_CTRL"
COMMAND_CHAR_UUID = "7b7d0002-2f4a-4f3d-9b4a-6a9d7f3c1000"
STATE_CHAR_UUID = "7b7d0003-2f4a-4f3d-9b4a-6a9d7f3c1000"


class ValveClient:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.client = None
        self.connected = False
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    async def connect(self):
        device = await BleakScanner.find_device_by_filter(
            lambda dev, adv: dev.name == DEVICE_NAME
            or (adv.local_name == DEVICE_NAME if adv else False),
            timeout=10.0,
        )

        if device is None:
            raise RuntimeError(f"BLE device not found: {DEVICE_NAME}")

        self.client = BleakClient(device, disconnected_callback=self._on_disconnect)
        await self.client.connect()
        self.connected = True
        return await self.read_state()

    def _on_disconnect(self, _client):
        self.connected = False

    async def toggle(self):
        self._check_connected()
        await self.client.write_gatt_char(COMMAND_CHAR_UUID, b"TOGGLE", response=True)
        return await self.read_state()

    async def read_state(self):
        self._check_connected()
        state = await self.client.read_gatt_char(STATE_CHAR_UUID)
        return state.decode("utf-8")

    async def disconnect(self):
        if self.client is not None and self.client.is_connected:
            await self.client.disconnect()
        self.connected = False

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    def _check_connected(self):
        if self.client is None or not self.client.is_connected:
            raise RuntimeError("BLE device is not connected")


class ValveApp:
    def __init__(self, root):
        self.root = root
        self.valve = ValveClient()

        self.root.title("ESP32-C3 Valve Control")
        self.root.geometry("320x180")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.status_var = tk.StringVar(value="Disconnected")
        self.state_var = tk.StringVar(value="GPIO10: --")

        tk.Label(root, textvariable=self.status_var, font=("Segoe UI", 11)).pack(pady=(18, 6))
        tk.Label(root, textvariable=self.state_var, font=("Segoe UI", 16, "bold")).pack(pady=6)

        self.toggle_button = tk.Button(
            root,
            text="Toggle GPIO10",
            font=("Segoe UI", 12),
            width=18,
            command=self.toggle,
            state=tk.DISABLED,
        )
        self.toggle_button.pack(pady=12)

        self.connect()

    def connect(self):
        self.status_var.set(f"Connecting to {DEVICE_NAME}...")
        future = self.valve.run(self.valve.connect())
        self.root.after(100, lambda: self._wait_for_connect(future))

    def _wait_for_connect(self, future):
        if not future.done():
            self.root.after(100, lambda: self._wait_for_connect(future))
            return

        try:
            state = future.result()
        except Exception as exc:
            self.status_var.set("Connection failed")
            messagebox.showerror("BLE Error", str(exc))
            return

        self.status_var.set("Connected")
        self.state_var.set(f"GPIO10: {state}")
        self.toggle_button.config(state=tk.NORMAL)

    def toggle(self):
        self.toggle_button.config(state=tk.DISABLED)
        self.status_var.set("Sending TOGGLE...")
        future = self.valve.run(self.valve.toggle())
        self.root.after(100, lambda: self._wait_for_toggle(future))

    def _wait_for_toggle(self, future):
        if not future.done():
            self.root.after(100, lambda: self._wait_for_toggle(future))
            return

        try:
            state = future.result()
        except Exception as exc:
            self.status_var.set("Disconnected")
            messagebox.showerror("BLE Error", str(exc))
            return

        self.status_var.set("Connected")
        self.state_var.set(f"GPIO10: {state}")
        self.toggle_button.config(state=tk.NORMAL)

    def close(self):
        future = self.valve.run(self.valve.disconnect())
        try:
            future.result(timeout=3)
        except Exception:
            pass
        self.valve.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    ValveApp(root)
    root.mainloop()
