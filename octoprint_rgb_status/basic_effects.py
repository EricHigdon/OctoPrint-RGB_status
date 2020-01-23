from rpi_ws281x import *
from .utils import blend_colors
import time


def run_effect(effect, lock, queue, strip, color, delay, reverse=False):
    lock.acquire()
    try:
        while queue.empty():
            effect(strip, color, queue, delay, reverse=reverse)
        while not queue.empty():
            queue.get()
    finally:
        lock.release()

# Define functions which animate LEDs in various ways.
def solid_color(strip, color, queue, delay=0, iterations=1, reverse=False):
    for p in range(strip.numPixels()):
        strip.setPixelColorRGB(p, *color)
    strip.show()


def color_wipe(strip, color, queue, delay=50, iterations=1, reverse=False):
    """Wipe color across display a pixel at a time."""
    pixels_range = range(strip.numPixels())
    if reverse:
        pixels_range = list(reversed(pixels_range))

    for i in range(iterations):
        for p in pixels_range:
            strip.setPixelColorRGB(p, *color)
            strip.show()
            if not queue.empty():
                return
            time.sleep(delay/100.0)
        for p in pixels_range:
            strip.setPixelColorRGB(p, 0, 0, 0)
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/100.0)


def theater_chase(strip, color, queue, delay=50, iterations=10, reverse=False):
    """Movie theater light style chaser animation."""
    pixels_range = range(0, strip.numPixels(), 3)
    if reverse:
        pixels_range = list(reversed(pixels_range))

    for i in range(iterations):
        for r in range(3):
            for p in pixels_range:
                strip.setPixelColorRGB(p+r, *color)
            strip.show()
            if not queue.empty():
                return
            time.sleep(delay/1000.0)
            for p in pixels_range:
                strip.setPixelColor(p+r, 0)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def rainbow(strip, color, queue, delay=20, iterations=1, reverse=False):
    """Draw rainbow that fades across all pixels at once."""
    for i in range(256*iterations):
        for p in range(strip.numPixels()):
            strip.setPixelColor(p, wheel((p+i) & 255))
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/1000.0)


def rainbow_cycle(strip, color, queue, delay=20, iterations=5, reverse=False):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for i in range(256*iterations):
        for p in range(strip.numPixels()):
            strip.setPixelColor(p, wheel((int(p * 256 / strip.numPixels()) + i) & 255))
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/1000.0)


def theater_chase_rainbow(strip, color, queue, delay=50, iterations=1, reverse=False):
    """Rainbow movie theater light style chaser animation."""
    for i in range(256*iterations):
        for r in range(3):
            for p in range(0, strip.numPixels(), 3):
                strip.setPixelColor(p+r, wheel((p+i) % 255))
            strip.show()
            if not queue.empty():
                return
            time.sleep(delay/1000.0)
            for p in range(0, strip.numPixels(), 3):
                strip.setPixelColor(p+r, 0)


def pulse(strip, color, queue, delay, iterations=1, reverse=False):
    for p in range(strip.numPixels()):
        strip.setPixelColorRGB(p, *color)
    for i in range(255):
        strip.setBrightness(i)
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/1000.0)
    for i in reversed(range(255)):
        strip.setBrightness(i)
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/1000.0)


def knight_rider(strip, color, queue, delay, iterations=1, reverse=False):
    for active_pixel in range(strip.numPixels()):
        for i in range(strip.numPixels()):
            if i == active_pixel or i+1 == active_pixel or i-1 == active_pixel:
                strip.setPixelColorRGB(i, *color)
            else:
                strip.setPixelColorRGB(i, *(0,0,0))
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/100.0)
    for active_pixel in reversed(range(strip.numPixels())):
        for i in range(strip.numPixels()):
            if i == active_pixel or i+1 == active_pixel or i-1 == active_pixel:
                strip.setPixelColorRGB(i, *color)
            else:
                strip.setPixelColorRGB(i, *(0,0,0))
        strip.show()
        if not queue.empty():
            return
        time.sleep(delay/100.0)
        
