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


def receive_image():
    buffer = bytearray(1)

    # confirm connection by sending 0x7A and waiting to recieve 0x7C
    print("checking connection...")
    start_time = time.monotonic()
    connecting = True
    connected = False
    buffer[0] = 0x7A

    # wait until confirmed UART connection with camera board
    while connecting:
        uart.write(buffer)
        curr_time = time.monotonic()
        if curr_time - 15 > start_time:
            # timed out
            connecting = False

        data = uart.read(1)

        if data is not None and 0x7C in data:
            connected = True
            connecting = False
            print("connection confirmed")
        time.sleep(1)
    if not connected:
        return None

    # if connection is confirmed request image by sending 0x7B
    start_time = time.monotonic()
    buffer[0] = 0x7B
    uart.write(buffer)
    retrieving = True
    current_file = "/sd/images/packeted_iamge_test.jpeg"

    """
    Option 1: packeting

    possible way of doing it, but having problems
    """
    while retrieving:
        curr_time = time.monotonic()
        if curr_time - 30 > start_time:
            # timed out
            return False

        data = uart.read(6000)

        if data is not None and len(data) > 1:
            print(f"packet recieved, header: {data[0]}, length: {len(data)}")
            if data[0] == 0xAA:
                # first packet
                # create new image file
                # if cubesat.rtc:
                #     t = cubesat.rtc.datetime
                # else:
                #     t = time.gmtime()
                try:
                    with open(current_file, "wb") as fd:
                        fd.write(data[1:])
                except Exception as e:
                    print(f"could not create new image file: {e}")
            elif data[0] == 0xAB:
                # middle packet
                try:
                    with open(current_file, "ab") as fd:
                        fd.write(data[1:])
                except Exception as e:
                    print(f"could not write mid packet to file: {e}")
            elif data[0] == 0xAC:
                # last packet
                retrieving = False
                try:
                    with open(current_file, "ab") as fd:
                        fd.write(data[1:])
                except Exception as e:
                    print(f"could not write last packet to file: {e}")
            # clear uart
            uart.reset_input_buffer()

            # send confirmation of recieved packet
            buffer[0] = 0xAD
            uart.write(buffer)
            del data
