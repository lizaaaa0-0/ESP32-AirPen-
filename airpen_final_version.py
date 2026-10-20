import pygame 
import serial
import time
import math


# ESP32 AIR PEN
# Hold the board like a pen: rotate your wrist
# to move, hold the button to draw.


PORT = "COM6"
BAUD = 115200

WIDTH, HEIGHT = 900, 600

# Sensor axis that runs along the breadboard's length
# (the direction the "pen tip" points). Try (1,0,0), (0,1,0),
# (0,0,1) or their negatives if directions feel wrong.
PEN_AXIS = (0.0, 1.0, 0.0)

# Cursor speed: pixels per degree of rotation. Use +/- to adjust.
SENS = 15.0

# Flip a direction if it moves the wrong way.
INVERT_X = 1
INVERT_Y = -1

# Ignore small gyro rates (deg/s) to reduce cursor drift while the board is still.
DEAD_RATE = 1.2

# Light smoothing of the rotation rate (0..1, higher = less smoothing).
RATE_SMOOTH = 0.5

# Canvas margins
MARGIN_X = 10
MARGIN_TOP = 50
MARGIN_BOTTOM = 10

# Drawing
LINE_WIDTH = 4
MIN_LINE_WIDTH = 1
MAX_LINE_WIDTH = 15

# Colors
BACKGROUND = (245, 245, 245)
CANVAS_COLOR = (255, 255, 255)
INK_COLOR = (20, 80, 220)
CURSOR_IDLE = (30, 170, 80)
CURSOR_DRAW = (220, 50, 50)
TEXT_COLOR = (30, 30, 30)

# ==========================================
# VECTOR HELPERS (no numpy needed)
# ==========================================

def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    n = norm(a)
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-9 else None


def calibrate(acc):
    """
    From the accelerometer (which reads 'up' at rest), build:
      up   = rotation about this axis -> left/right
      side = up x pen axis -> rotation about this axis -> up/down
    Returns None if the pen points straight up/down (side axis undefined).
    """
    up = unit(acc)
    if up is None:
        return None
    side = cross(up, PEN_AXIS)
    if norm(side) < 0.3:
        return None
    return up, unit(side)


def deadzone(value, limit):
    if abs(value) < limit:
        return 0.0
    return value - limit if value > 0 else value + limit


def clamp(value, low, high):
    return max(low, min(high, value))


def parse_line(line):
    """gx,gy,gz,ax,ay,az,draw,dt"""
    parts = line.strip().split(",")
    if len(parts) != 8:
        return None
    try:
        v = [float(p) for p in parts]
    except ValueError:
        return None
    gyro = (v[0], v[1], v[2])
    acc = (v[3], v[4], v[5])
    draw = int(v[6])
    dt = v[7]
    return gyro, acc, draw, dt


# ==========================================
# INITIALIZE PYGAME
# ==========================================

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ESP32 Air Pen - V3")

font = pygame.font.SysFont(None, 25)
small_font = pygame.font.SysFont(None, 21)

canvas = pygame.Surface((WIDTH, HEIGHT))
canvas.fill(CANVAS_COLOR)
clock = pygame.time.Clock()

# ==========================================
# CONNECT TO ESP32
# ==========================================

try:
    ser = serial.Serial(PORT, BAUD, timeout=0.01)
    time.sleep(2)
    ser.reset_input_buffer()
except serial.SerialException as error:
    print("Could not open ESP32 serial port:", error)
    pygame.quit()
    raise SystemExit

# ==========================================
# STATE
# ==========================================

x_min, x_max = MARGIN_X, WIDTH - MARGIN_X
y_min, y_max = MARGIN_TOP, HEIGHT - MARGIN_BOTTOM

x = WIDTH / 2
y = (y_min + y_max) / 2

acc_avg = None        # smoothed accelerometer, used for calibration
axes = None           # (up, side) once calibrated
rate_yaw = 0.0
rate_pitch = 0.0

drawing = False
last_point = None
sensor_ready = False
running = True

# ==========================================
# MAIN LOOP
# ==========================================

try:
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_c:
                    canvas.fill(CANVAS_COLOR)
                    last_point = None

                elif event.key == pygame.K_r:
                    # Hold the pen still in your writing pose, then press R.
                    if acc_avg is not None:
                        axes = calibrate(acc_avg)
                    x = WIDTH / 2
                    y = (y_min + y_max) / 2
                    last_point = None

                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    SENS = min(60.0, SENS + 2.0)

                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    SENS = max(4.0, SENS - 2.0)

                elif event.key == pygame.K_RIGHTBRACKET:
                    LINE_WIDTH = min(MAX_LINE_WIDTH, LINE_WIDTH + 1)

                elif event.key == pygame.K_LEFTBRACKET:
                    LINE_WIDTH = max(MIN_LINE_WIDTH, LINE_WIDTH - 1)

        # ----------------------------------
        # READ *EVERY* PACKET (rates must be integrated, not skipped)
        # ----------------------------------

        while ser.in_waiting:
            line = ser.readline().decode("utf-8", errors="ignore")
            data = parse_line(line)
            if data is None:
                continue

            gyro, acc, draw, dt = data
            sensor_ready = True
            drawing = (draw == 1)

            # Slow average of accel = gravity direction.
            if acc_avg is None:
                acc_avg = acc
            else:
                acc_avg = tuple(a + (b - a) * 0.05 for a, b in zip(acc_avg, acc))
                
            if axes is None:
                axes = calibrate(acc_avg)

            if axes is None or not (0.0 < dt < 0.1):
                continue

            up, side = axes
            yaw = deadzone(dot(gyro, up), DEAD_RATE)       # left/right
            pitch = deadzone(dot(gyro, side), DEAD_RATE)   # up/down

            rate_yaw += (yaw - rate_yaw) * RATE_SMOOTH
            rate_pitch += (pitch - rate_pitch) * RATE_SMOOTH

            x += -rate_yaw * dt * SENS * INVERT_X
            y += rate_pitch * dt * SENS * INVERT_Y
            x = clamp(x, x_min, x_max)
            y = clamp(y, y_min, y_max)

        point = (int(x), int(y))

        # ----------------------------------
        # DRAWING
        # ----------------------------------

        if drawing and sensor_ready and axes is not None:
            if last_point is not None:
                pygame.draw.line(canvas, INK_COLOR, last_point, point, LINE_WIDTH)
            else:
                pygame.draw.circle(canvas, INK_COLOR, point, max(1, LINE_WIDTH // 2))
            last_point = point
        else:
            last_point = None

        # ----------------------------------
        # DISPLAY
        # ----------------------------------

        screen.fill(BACKGROUND)
        screen.blit(canvas, (0, 0))

        pygame.draw.circle(
            screen, CURSOR_DRAW if drawing else CURSOR_IDLE, point, 7
        )

        if not sensor_ready:
            status = "Waiting for ESP32 sensor data..."
        elif axes is None:
            status = "Tilt the pen toward the screen, hold still, press R"
        elif drawing:
            status = "DRAWING"
        else:
            status = "MOVING - pen lifted"

        screen.blit(font.render(status, True, TEXT_COLOR), (15, 10))
        screen.blit(
            small_font.render(
                f"Speed: {SENS:.0f} px/deg  |  Brush: {LINE_WIDTH}px",
                True, TEXT_COLOR),
            (15, 32))
        screen.blit(
            small_font.render(
                "Hold button: Draw | +/-: Speed | [ ]: Brush | "
                "C: Clear | R: Calibrate | ESC: Quit",
                True, TEXT_COLOR),
            (15, HEIGHT - 25))

        pygame.display.flip()
        clock.tick(60)

finally:
    ser.close()
    pygame.quit()