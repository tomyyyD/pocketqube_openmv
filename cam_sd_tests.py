# Untitled - By: tbdamiani - Tue Jun 13 2023

import sensor, image, time, os

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.HD)         # HD is 1280 x 720
sensor.skip_frames(time = 2000)

clock = time.clock()

print(os.listdir())

try:
    if not "images" in os.listdir():
        os.mkdir("images")
except Exception as e:
    print(f"could not create images directory: {e}")

while(True):
    t = time.gmtime()
    timestamp = f'{t[0]:04}.{t[1]:02}.{t[2]:02}.{t[3]:02}.{t[4]:02}.{t[5]:02}'
    img = sensor.snapshot()
    img = img.compress(quality=40)
    img.save(f"images/{timestamp}.jpeg")
    print(os.listdir("images"))
    time.sleep(5)
