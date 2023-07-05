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


def handle_disk_send(filepath):
    # gets stat.ST_SIZE
    filesize = os.stat(filepath)[6]
    packet_len = 5120
    pointer = 0
    with open(filepath, "rb") as fd:
        while (pointer < filesize):
            fd.seek(pointer)
            data = fd.read(packet_len - 1)
            packet = bytearray(len(data) + 1)

            if filesize < pointer + packet_len:
                # last packet
                packet[0] = 0xAC
            elif pointer == 0:
                # first packet
                packet[0] = 0xAA
            else:
                # mid packet
                packet[0] = 0xAB
            packet[1:] = data

            uart.write(packet)
            pointer += (packet_len - 1)

            # wait for confirmation
            confirmed = False
            s_time = time.time()
            buffer = bytearray(1)
            while not confirmed:
                if time.time() - 10 > s_time:
                    return False
                if uart.any():
                    uart.readinto(buffer)
                    if buffer[0] == 0xAD:
                        confirmed = True
                        time.sleep(0.3)
    return True


def handle_memory_send(img):
    uart.write(img)
    s_time = time.time()
    buffer = bytearray(1)
    confirmed = False
    while not confirmed:
        if time.time() - 20 > s_time:
            return False
        if uart.any():
            uart.readinto(buffer)
            if buffer[0] == 0xAD:
                confirmed = True
    return True


try:
    if "images" not in os.listdir():
        os.mkdir("images")
except Exception as e:
    print(f"could not create images directory: {e}")


buffer = bytearray(1)
while (True):
    if (uart.any()):
        uart.readinto(buffer)
        if (0x7A == buffer[0]):
            # confirm connection
            buffer[0] = 0x7C
            uart.write(buffer)
        if (buffer[0] == 0x7B):
            # send image
            for i in range(10):
                sensor.snapshot()
            img = sensor.snapshot()
            filename = "images/image_test.jpeg"
            img.save(filename, quality=50)
            handle_disk_send(filename)
