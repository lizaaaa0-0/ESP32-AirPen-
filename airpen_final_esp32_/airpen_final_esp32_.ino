#include <Wire.h>

const int SDA_PIN = 21;
const int SCL_PIN = 22;
const int BUTTON_PIN = 18;

const uint8_t MPU_ADDR = 0x68;

const unsigned long LOOP_US = 10000;   // 100 Hz fixed loop
const float GYRO_SCALE = 65.5;         // LSB per deg/s at +/-500 deg/s
const float ACCEL_SCALE = 16384.0;     // LSB per g at +/-2 g

float gyroBias[3] = {0, 0, 0};
unsigned long lastTime;

bool writeRegister(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

bool readRegisters(uint8_t reg, uint8_t count, uint8_t *data) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU_ADDR, count) != count) return false;
  for (uint8_t i = 0; i < count; i++) data[i] = Wire.read();
  return true;
}

int16_t combineBytes(uint8_t high, uint8_t low) {
  return (int16_t)((uint16_t)high << 8 | low);
}

// Average all three gyro axes while the board is still.
void calibrateGyro() {
  const int samples = 300;
  float sum[3] = {0, 0, 0};
  int good = 0;

  for (int i = 0; i < samples; i++) {
    uint8_t d[14];
    if (readRegisters(0x3B, 14, d)) {
      sum[0] += combineBytes(d[8], d[9]) / GYRO_SCALE;
      sum[1] += combineBytes(d[10], d[11]) / GYRO_SCALE;
      sum[2] += combineBytes(d[12], d[13]) / GYRO_SCALE;
      good++;
    }
    delay(3);
  }

  if (good > 0) {
    for (int i = 0; i < 3; i++) gyroBias[i] = sum[i] / good;
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  delay(100);

  if (!writeRegister(0x6B, 0x00)) {
    Serial.println("ERROR: MPU6050 not found");
    while (true) delay(1000);
  }

  writeRegister(0x1A, 0x03);  // low-pass filter
  writeRegister(0x1B, 0x08);  // gyro +/-500 deg/s
  writeRegister(0x1C, 0x00);  // accel +/-2 g

  uint8_t who;
  if (!readRegisters(0x75, 1, &who) || (who != 0x68 && who != 0x70)) {
    Serial.println("ERROR: Unexpected MPU identity");
    while (true) delay(1000);
  }

  delay(500);
  calibrateGyro();            // keep the board still (~1 s)

  Serial.println("gx,gy,gz,ax,ay,az,draw,dt");
  lastTime = micros();
}

void loop() {
  unsigned long now = micros();
  if (now - lastTime < LOOP_US) return;

  float dt = (now - lastTime) / 1000000.0;
  lastTime = now;

  uint8_t d[14];
  if (!readRegisters(0x3B, 14, d)) return;

  float ax = combineBytes(d[0], d[1]) / ACCEL_SCALE;
  float ay = combineBytes(d[2], d[3]) / ACCEL_SCALE;
  float az = combineBytes(d[4], d[5]) / ACCEL_SCALE;

  float gx = combineBytes(d[8], d[9]) / GYRO_SCALE - gyroBias[0];
  float gy = combineBytes(d[10], d[11]) / GYRO_SCALE - gyroBias[1];
  float gz = combineBytes(d[12], d[13]) / GYRO_SCALE - gyroBias[2];

  int draw = (digitalRead(BUTTON_PIN) == LOW) ? 1 : 0;

  // CSV: gx,gy,gz (deg/s), ax,ay,az (g), draw, dt (s)
  char buf[96];
  snprintf(buf, sizeof(buf), "%.2f,%.2f,%.2f,%.3f,%.3f,%.3f,%d,%.4f",
           gx, gy, gz, ax, ay, az, draw, dt);
  Serial.println(buf);
}