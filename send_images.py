import time
import os
import sys
import board
import storage
import busio
import sdcardio
import digitalio

uart = busio.UART(board.TX, board.RX, baudrate=115200)

try:
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
except Exception as e:
    print(f"failed to init SPI: {e}")

try:
    sd = sdcardio.SDCard(spi, board.SD_CS, baudrate=4000000)
except Exception as e:
    print(f"failed to init SD: {e}")

try:
    vfs = storage.VfsFat(sd)
    storage.mount(vfs, "/sd")
    sys.path.append("/sd")
except Exception as e:
    print('[ERROR][Initializing VFS]', e)

try:
    os.mkdir("/sd/images")
except Exception as e:
    print(f"error creating img folder: {e}")

cam_pin = digitalio.DigitalInOut(board.CAM_EN)
cam_pin.direction = digitalio.Direction.OUTPUT

last_time = time.monotonic()

img_no = 0

buffer = bytearray(1)
while True:
    current_time = time.monotonic()
    if last_time + 10 < current_time:
        cam_pin.value = True
        print("requesting...")
        buffer[0] = 0x7B
        uart.write(buffer)
        last_time = current_time

    data = uart.read(30000)

    if data is not None and len(data) > 1:
        try:
            with open(f"/sd/images/image_{img_no}.jpeg", "wb") as fd:
                fd.write(data)
                img_no += 1
        except Exception as e:
            print(f"couldn't store file: {e}")
        index = 0
        cam_pin.value = False
        print(f"...recieved {len(data)} bytes")

        time.sleep(3)
