# Displays the MicroPython logo on an SSD1677 e-paper display.
#
# Run this from the directory containing micropython_logo.bin (or adjust
# LOGO_PATH below), with ssd1677.py available on the device.

from machine import Pin, SPI
import framebuf
import ssd1677

LOGO_PATH = "micropython_logo.bin"
LOGO_WIDTH = 312
LOGO_HEIGHT = 318

spi = SPI(1, baudrate=4_000_000, polarity=0, phase=0, sck=Pin.board.EPD_SCK, mosi=Pin.board.EPD_MOSI)

epd = ssd1677.SSD1677(
    800,
    480,
    spi,
    dc=Pin(Pin.board.EPD_DC),
    cs=Pin(Pin.board.EPD_CS),
    rst=Pin(Pin.board.EPD_RST),
    busy=Pin(Pin.board.EPD_BUSY),
)

with open(LOGO_PATH, "rb") as f:
    logo_buf = bytearray(f.read())
logo = framebuf.FrameBuffer(logo_buf, LOGO_WIDTH, LOGO_HEIGHT, framebuf.MONO_HLSB)

epd.fill(0)
x = (epd.width - LOGO_WIDTH) // 2
y = (epd.height - LOGO_HEIGHT) // 2 - 10
epd.blit(logo, x, y)
epd.text("MicroPython", x + 60, y + LOGO_HEIGHT + 10, 1)
epd.show()
