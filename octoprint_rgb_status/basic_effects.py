from rpi_ws281x import *
import time


def run_effect(effect, lock, queue, strip, color, delay):
    while True:
        lock.acquire()
        try:
            if not queue.empty():
                msg = queue.get()
                if msg == 'KILL':
                    raise Exception
            effect(strip, color, delay)
        except:
            break
        finally:
            lock.release()

# Define functions which animate LEDs in various ways.
def solid_color(strip, color, delay=0, iterations=1):
    for p in range(strip.numPixels()):
        strip.setPixelColorRGB(p, *color)
    strip.show()


def color_wipe(strip, color, delay=50, iterations=1):
    """Wipe color across display a pixel at a time."""
    for i in range(iterations):
        for p in range(strip.numPixels()):
            strip.setPixelColorRGB(p, *color)
            strip.show()
            time.sleep(delay/1000.0)
        for p in range(strip.numPixels()):
            strip.setPixelColorRGB(p, 0, 0, 0)
        strip.show()
        time.sleep(delay/1000.0)


def theater_chase(strip, color, delay=50, iterations=10):
    """Movie theater light style chaser animation."""
    for i in range(iterations):
        for r in range(3):
            for p in range(0, strip.numPixels(), 3):
                strip.setPixelColorRGB(p+r, *color)
            strip.show()
            time.sleep(delay/1000.0)
            for p in range(0, strip.numPixels(), 3):
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


def rainbow(strip, color=None, delay=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for i in range(256*iterations):
        for p in range(strip.numPixels()):
            strip.setPixelColor(p, wheel((p+i) & 255))
        strip.show()
        time.sleep(delay/1000.0)


def rainbow_cycle(strip, color=None, delay=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for i in range(256*iterations):
        for p in range(strip.numPixels()):
            strip.setPixelColor(p, wheel((int(p * 256 / strip.numPixels()) + i) & 255))
        strip.show()
        time.sleep(delay/1000.0)


def theater_chase_rainbow(strip, color=None, delay=50, iterations=1):
    """Rainbow movie theater light style chaser animation."""
    for i in range(256*iterations):
        for r in range(3):
            for p in range(0, strip.numPixels(), 3):
                strip.setPixelColor(p+r, wheel((p+i) % 255))
            strip.show()
            time.sleep(delay/1000.0)
            for p in range(0, strip.numPixels(), 3):
                strip.setPixelColor(p+r, 0)
