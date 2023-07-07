import time
import sensor
import os
from pyb import UART

# set up camera
sensor.reset()                          # Reset and initialize the sensor.
sensor.set_pixformat(sensor.RGB565)     # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.HD)         # Set frame size to HD (640 x 480)
sensor.skip_frames(time=2000)           # Wait for settings take effect.

# UART 3, and baudrate.
uart = UART(3, 115200)

#constants
CONFIRMATION_SEND_CODE = 0xAA
CONFIRMATION_RECEIVE_CODE = 0xAB
IMAGE_START = 0xAC
IMAGE_MID = 0xAD
IMAGE_END = 0xAE
IMAGE_CONF = 0xAF
PACKET_REQ = 0xB0

filepath = "images/image_test.jpeg"

try:
    if "images" not in os.listdir():
        os.mkdir("images")
except Exception as e:
    print(f"could not create images directory: {e}")


buffer = bytearray(1)
confirmed = False
while not confirmed:
    buffer[0] = CONFIRMATION_SEND_CODE
    print(f"writing: {buffer}")
    uart.write(buffer)
    start_time = time.ticks_ms()
    while time.ticks_ms() - 1000 < start_time:
        uart.readinto(buffer)
        if buffer[0] == CONFIRMATION_RECEIVE_CODE:
            img = sensor.snapshot()
            img.save(filepath, quality=50)
            # connection confirmed and begin sending message
            confirmed = True


# send packets and wait for ack after each packet
# gets stat.ST_SIZE
filesize = os.stat(filepath)[6]
packet_len = 500
pointer = 0
while (pointer < filesize):
    sleeping = True
    while(sleeping):
        uart.readinto(buffer)
        if buffer[0] == PACKET_REQ:
            print("writing packet")
            sleeping = False

    with open(filepath, "rb") as fd:
        fd.seek(pointer)
        data = fd.read(packet_len - 1)
    packet = bytearray(len(data) + 1)

    if filesize < pointer + packet_len:
        # last packet
        packet[0] = IMAGE_END
    elif pointer == 0:
        # first packet
        packet[0] = IMAGE_START
    else:
        # mid packet
        packet[0] = IMAGE_MID
    packet[1:] = data
    print(packet)
    uart.write(packet)

    # wait for confirmation
    confirmed = False
    s_time = time.ticks_ms()
    buffer = bytearray(1)
    while not confirmed:
        if time.ticks_ms() - 10000 > s_time:
            break
        if uart.any():
            uart.readinto(buffer)
            if buffer[0] == IMAGE_CONF:
                print("packet confirmed")
                pointer += (packet_len - 1)
                confirmed = True
