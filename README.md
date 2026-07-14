# micropython-ssd1677

A pure MicroPython, [`framebuf.FrameBuffer`](https://docs.micropython.org/en/latest/library/framebuf.html)-based
driver for the SSD1677 e-paper display controller, as used in 800x480
monochrome panels such as the one in the [Xteink X4](https://www.xteink.com/products/xteink-x4)
e-reader.

Three refresh modes are supported:
- `show()` — full refresh (~1.6s). Slowest, but no ghosting; visibly flashes.
- `show_partial()` — refreshes only the region changed since the last
  `show*()` call (tracked automatically). Much quicker (~0.7s measured) and
  low-flicker, but ghosting accumulates over repeated use.
- `show_fast()` — full-screen refresh using the panel's alternate waveform.
  On the Xteink X4 panel this measured about the same speed as `show()`
  (~1.6s) — the expected speedup didn't show up on this particular panel's
  OTP waveform table. `show_partial()` is the more reliable way to get a
  snappier update; `show_fast()` is kept since it may behave differently on
  other SSD1677 panels.

Ghosting from `show_partial()`/`show_fast()` isn't cleared automatically —
call `show()` periodically (e.g. every N partial updates) to reset it.

## Install

```python
import mip
mip.install("github:mattytrentini/micropython-ssd1677")
```

## Usage

```python
from machine import Pin, SPI
import ssd1677

spi = SPI(1, baudrate=4_000_000, polarity=0, phase=0, sck=Pin(8), mosi=Pin(10))

epd = ssd1677.SSD1677(
    800,
    480,
    spi,
    dc=Pin(4),
    cs=Pin(21),
    rst=Pin(5),
    busy=Pin(6),
)

epd.fill(0)
epd.text("Hello, e-paper!", 10, 10, 1)
epd.show()
```

`SSD1677` subclasses `framebuf.FrameBuffer`, so all the usual drawing methods
(`pixel`, `line`, `rect`, `fill_rect`, `text`, `blit`, etc.) are available.
Color `1` draws black (ink), color `0` is white (background) — the driver
handles the panel's own inverted RAM convention internally.

No MISO connection is needed; this driver only ever writes to the panel.

There's no rotation support: the framebuffer is always in the panel's native
800(w)x480(h) raster, regardless of how the panel is physically mounted in a
device. If your device holds the panel rotated relative to its native
orientation (as the Xteink X4 does), rotating drawn content is left to the
caller for now.

## Acknowledgements

The SSD1677 command sequence was cross-referenced from
[Adafruit's CircuitPython SSD1677 driver](https://github.com/adafruit/Adafruit_CircuitPython_SSD1677)
and [Waveshare's `epd4in26.py` reference driver](https://github.com/waveshareteam/e-Paper),
which is the vendor-native source both this driver and Adafruit's are
ultimately based on.

## License

MIT, see [LICENSE](LICENSE).
