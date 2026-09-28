#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

const int VALVE_PIN = 10;

const char *DEVICE_NAME = "ESP32C3_VALVE_CTRL";
const char *SERVICE_UUID = "7b7d0001-2f4a-4f3d-9b4a-6a9d7f3c1000";
const char *COMMAND_CHAR_UUID = "7b7d0002-2f4a-4f3d-9b4a-6a9d7f3c1000";
const char *STATE_CHAR_UUID = "7b7d0003-2f4a-4f3d-9b4a-6a9d7f3c1000";

BLECharacteristic *stateCharacteristic = nullptr;
bool valveStateHigh = false;

void publishState() {
  const char *stateText = valveStateHigh ? "HIGH" : "LOW";
  stateCharacteristic->setValue(stateText);
}

void setValveState(bool high) {
  valveStateHigh = high;
  digitalWrite(VALVE_PIN, valveStateHigh ? HIGH : LOW);
  publishState();
}

class CommandCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *characteristic) override {
    String command = characteristic->getValue().c_str();
    command.trim();
    command.toUpperCase();

    if (command == "TOGGLE") {
      setValveState(!valveStateHigh);
    }
  }
};

class ServerCallbacks : public BLEServerCallbacks {
  void onDisconnect(BLEServer *server) override {
    BLEDevice::startAdvertising();
  }
};

void setup() {
  pinMode(VALVE_PIN, OUTPUT);
  digitalWrite(VALVE_PIN, LOW);

  BLEDevice::init(DEVICE_NAME);

  BLEServer *server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());

  BLEService *service = server->createService(SERVICE_UUID);

  BLECharacteristic *commandCharacteristic = service->createCharacteristic(
      COMMAND_CHAR_UUID,
      BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
  commandCharacteristic->setCallbacks(new CommandCallbacks());

  stateCharacteristic = service->createCharacteristic(
      STATE_CHAR_UUID,
      BLECharacteristic::PROPERTY_READ);

  setValveState(false);

  service->start();

  BLEAdvertising *advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(SERVICE_UUID);
  advertising->setScanResponse(true);
  advertising->setMinPreferred(0x06);
  advertising->setMinPreferred(0x12);

  BLEDevice::startAdvertising();
}

void loop() {
  delay(1000);
}
