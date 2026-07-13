# micropython-ssd1677

A pure MicroPython, [`framebuf.FrameBuffer`](https://docs.micropython.org/en/latest/library/framebuf.html)-based
driver for the SSD1677 e-paper display controller, as used in 800x480
monochrome panels such as the one in the [Xteink X4](https://www.xteink.com/products/xteink-x4)
e-reader.

Only full-refresh updates are currently supported. The panel also supports
fast and partial refresh modes, but those aren't implemented yet.

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

A full refresh (`show()`) takes roughly 1.6 seconds and will visibly flash
the screen — this is normal for e-paper.

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
