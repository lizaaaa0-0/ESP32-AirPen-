#  ESP32 AirPen

**A motion-sensing air-writing pen built with ESP32, MPU6050, and webcam-assisted computer vision.**

ESP32-AirPen is a DIY electronic pen that allows users to write and draw in the air and visualize their movements as digital strokes on a computer. It combines embedded systems, inertial motion sensing, and computer vision to create an interactive writing experience.

##  Features

*  Air writing and digital drawing
*  ESP32-based motion data acquisition
*  MPU6050 accelerometer and gyroscope integration
*  Webcam-assisted pen position tracking
*  Physical button for drawing control
*  Python-based processing and visualization
*  OpenCV-based visual tracking
*  Serial communication between the ESP32 and computer

##  Hardware Components

* ESP32 DevKit Module
* MPU6050 accelerometer and gyroscope module
* Momentary push button
* Jumper wires
* Breadboard for prototyping
* USB cable
* Laptop with a built-in webcam
* Colored marker or tape for visual tracking

##  Software and Technologies

* **Arduino IDE:** ESP32 firmware development
* **C++:** Embedded programming
* **Python:** Data processing and drawing logic
* **OpenCV:** Webcam access and marker tracking
* **NumPy:** Image processing and numerical operations
* **PySerial:** Serial communication between the ESP32 and Python

##  How It Works

1. The MPU6050 measures the pen's acceleration and angular velocity.
2. The ESP32 reads the sensor data and monitors the physical button.
3. Sensor readings and button states are transmitted to the computer.
4. The webcam tracks a visible marker attached to the pen to estimate its position in the camera image.
5. Python processes the tracking data and button state to produce digital strokes on the screen.

The webcam provides 2D position tracking, while the MPU6050 supplies additional motion and orientation information.

##  Hardware Connections

Typical connections for an ESP32 DevKit V1:

| Component   | ESP32 Pin       |
| ----------- | --------------- |
| MPU6050 VCC | 3V3             |
| MPU6050 GND | GND             |
| MPU6050 SDA | GPIO 21         |
| MPU6050 SCL | GPIO 22         |
| Push button | GPIO 18 and GND |

*Note: These are the standard connections for this implementation. Check the firmware if your actual wiring uses different pins.*

##  Installation and Setup

### 1. ESP32 Firmware

1. Install the Arduino IDE and configure ESP32 board support.
2. Install the required MPU6050 libraries.
3. Connect the ESP32 to your computer using USB.
4. Open the AirPen firmware in the Arduino IDE.
5. Select the correct ESP32 board and serial port.
6. Upload the firmware.

### 2. Python Environment

Install Python and the required libraries:

```bash
python -m pip install opencv-python numpy pyserial
```

### 3. Configure and Run

1. Connect the ESP32 and identify its serial port.
2. Close the Arduino Serial Monitor before running the Python program.
3. Configure the Python code to use the correct serial port and webcam.
4. Ensure the tracking marker is clearly visible to the camera.
5. Launch the Python application and use the physical button to control drawing.

Refer to the source files in this repository for the exact firmware, configuration, and execution steps.



##  Technical Overview

The MPU6050 measures acceleration and angular velocity, but it does not directly measure absolute position. Estimating position by integrating acceleration can accumulate significant errors over time.

To improve writing accuracy, the system uses webcam-based visual tracking as its primary source of 2D position information. The ESP32 and MPU6050 provide additional motion data, while Python coordinates the input and drawing process.

##  Applications

* Gesture-based computer interaction
* Experimental digital handwriting
* Embedded systems and sensor integration
* Computer vision learning
* Motion tracking and human-computer interaction

##  Possible Future Improvements

* Wireless communication using Bluetooth or Wi-Fi
* Improved tracking and motion filtering
* Sensor fusion for enhanced orientation estimation
* Pressure-sensitive or multi-button controls
* Custom enclosure and portable power supply
* Improved calibration and handwriting smoothness

##  Project Purpose

This project explores the integration of microcontrollers, inertial sensors, and computer vision to develop an affordable air-writing interface.

It demonstrates practical concepts in embedded programming, sensor interfacing, serial communication, image processing, and human-computer interaction.



**Built with ESP32, MPU6050, Python, and OpenCV.** 