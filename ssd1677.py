# MicroPython SSD1677 e-paper display driver (SPI)
#
# For 800x480 monochrome panels such as the one used in the Xteink X4
# e-reader. Only full-screen, full-refresh updates are supported; the panel
# also supports fast and partial refresh modes but those aren't implemented
# here yet.
#
# Framebuffer convention: color 1 = black (ink), color 0 = white (background),
# matching typical framebuf usage elsewhere. This is the *opposite* of the
# panel's own RAM convention (a RAM bit of 1 renders white, 0 renders black),
# so the buffer is inverted on the way out in show().
#
# No rotation support: the framebuffer is always in the panel's native
# 800(w)x480(h) raster. On devices where the panel is mounted rotated
# relative to how it's held (e.g. a landscape panel used for portrait
# reading), rotating the drawn content is left to the caller for now.

import time
import framebuf
from micropython import const

_SW_RESET = const(0x12)
_TEMP_SENSOR_CONTROL = const(0x18)
_BOOSTER_SOFT_START = const(0x0C)
_DRIVER_OUTPUT_CONTROL = const(0x01)
_BORDER_WAVEFORM_CONTROL = const(0x3C)
_DATA_ENTRY_MODE = const(0x11)
_SET_RAM_X_WINDOW = const(0x44)
_SET_RAM_Y_WINDOW = const(0x45)
_SET_RAM_X_COUNTER = const(0x4E)
_SET_RAM_Y_COUNTER = const(0x4F)
_WRITE_RAM_BW = const(0x24)
_DISPLAY_UPDATE_CONTROL_2 = const(0x22)
_MASTER_ACTIVATION = const(0x20)
_DEEP_SLEEP = const(0x10)

_UPDATE_MODE_FULL = const(0xF7)

_BUSY_POLL_MS = const(20)
_BUSY_TIMEOUT_MS = const(15000)


class SSD1677(framebuf.FrameBuffer):
    def __init__(self, width, height, spi, dc, cs, rst, busy):
        if width % 8:
            raise ValueError("width must be a multiple of 8")

        self.width = width
        self.height = height
        self.spi = spi
        self.dc = dc
        self.cs = cs
        self.rst = rst
        self.busy = busy

        self.dc.init(self.dc.OUT, value=0)
        self.cs.init(self.cs.OUT, value=1)
        self.rst.init(self.rst.OUT, value=1)
        self.busy.init(self.busy.IN)

        self.buffer = bytearray(width // 8 * height)
        super().__init__(self.buffer, width, height, framebuf.MONO_HLSB)

        self.init_display()

    def _cmd(self, command, *data):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([command]))
        if data:
            self.dc(1)
            self.spi.write(bytearray(data))
        self.cs(1)

    def _busy_wait(self):
        t0 = time.ticks_ms()
        while self.busy.value():
            if time.ticks_diff(time.ticks_ms(), t0) > _BUSY_TIMEOUT_MS:
                raise OSError("SSD1677: timed out waiting for busy")
            time.sleep_ms(_BUSY_POLL_MS)
        time.sleep_ms(_BUSY_POLL_MS)

    def _reset(self):
        self.rst(1)
        time.sleep_ms(20)
        self.rst(0)
        time.sleep_ms(2)
        self.rst(1)
        time.sleep_ms(20)

    def _set_window(self, x_start, y_start, x_end, y_end):
        self._cmd(
            _SET_RAM_X_WINDOW,
            x_start & 0xFF,
            (x_start >> 8) & 0x03,
            x_end & 0xFF,
            (x_end >> 8) & 0x03,
        )
        self._cmd(
            _SET_RAM_Y_WINDOW,
            y_start & 0xFF,
            (y_start >> 8) & 0xFF,
            y_end & 0xFF,
            (y_end >> 8) & 0xFF,
        )

    def _set_cursor(self, x, y):
        self._cmd(_SET_RAM_X_COUNTER, x & 0xFF, (x >> 8) & 0x03)
        self._cmd(_SET_RAM_Y_COUNTER, y & 0xFF, (y >> 8) & 0xFF)

    def init_display(self):
        self._reset()
        self._busy_wait()

        self._cmd(_SW_RESET)
        self._busy_wait()

        self._cmd(_TEMP_SENSOR_CONTROL, 0x80)
        self._cmd(_BOOSTER_SOFT_START, 0xAE, 0xC7, 0xC3, 0xC0, 0x80)

        h = self.height
        self._cmd(_DRIVER_OUTPUT_CONTROL, (h - 1) & 0xFF, ((h - 1) >> 8) & 0xFF, 0x02)
        self._cmd(_BORDER_WAVEFORM_CONTROL, 0x01)
        self._cmd(_DATA_ENTRY_MODE, 0x01)  # X increment, Y decrement

        self._set_window(0, h - 1, self.width - 1, 0)
        self._set_cursor(0, 0)
        self._busy_wait()

    def show(self):
        """Push the framebuffer to the display and do a full refresh."""
        h = self.height
        self._set_window(0, h - 1, self.width - 1, 0)
        self._set_cursor(0, 0)

        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([_WRITE_RAM_BW]))
        self.dc(1)
        # Panel RAM uses the opposite polarity to our framebuffer (1=white,
        # 0=black), so invert each byte on the way out. Streamed in chunks
        # to avoid allocating a second full-size copy of the buffer.
        chunk = bytearray(512)
        mv = memoryview(self.buffer)
        for offset in range(0, len(mv), len(chunk)):
            piece = mv[offset : offset + len(chunk)]
            for i, b in enumerate(piece):
                chunk[i] = b ^ 0xFF
            self.spi.write(memoryview(chunk)[: len(piece)])
        self.cs(1)

        self._cmd(_DISPLAY_UPDATE_CONTROL_2, _UPDATE_MODE_FULL)
        self._cmd(_MASTER_ACTIVATION)
        self._busy_wait()

    def sleep(self):
        """Put the panel into deep sleep. A hardware reset is needed to wake it."""
        self._cmd(_DEEP_SLEEP, 0x01)
        time.sleep_ms(2000)
