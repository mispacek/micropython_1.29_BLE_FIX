# SPDX-License-Identifier: MIT
# Copyright (c) 2019-2026 Milan Spacek
# ESP IDE: https://espide.eu
# Simple multiple OLED display driver for MicroPython

from micropython import const
import framebuf

# ===== command registers (from the SSD1306 datasheet) =====
SET_CONTRAST       = const(0x81)
SET_ENTIRE_ON      = const(0xA4)
SET_NORM_INV       = const(0xA6)
SET_DISP           = const(0xAE)
SET_MEM_ADDR       = const(0x20)
SET_DISP_START_LINE= const(0x40)
SET_SEG_REMAP      = const(0xA0)  # +1 remaps SEG0 to column 127
SET_MUX_RATIO      = const(0xA8)
SET_COM_OUT_DIR    = const(0xC0)  # scan from COM0 to COM[N]
SET_DISP_OFFSET    = const(0xD3)
SET_COM_PIN_CFG    = const(0xDA)
SET_DISP_CLK_DIV   = const(0xD5)
SET_PRECHARGE      = const(0xD9)
SET_VCOM_DESEL     = const(0xDB)
SET_CHARGE_PUMP    = const(0x8D)

class OLED128x64(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, buffer=None, addr=0x3C, rotate=False,
                 controller="ssd1306", col_offset=None):
        self.width  = width
        self.height = height
        self.pages  = height // 8
        self.i2c    = i2c
        self.addr   = addr
        self.rotate = rotate
        self.controller = (controller or "ssd1306").lower()
        self.last_error = None

        if self.controller not in ("ssd1306", "ssd1309", "sh1106"):
            raise ValueError("controller must be ssd1306, ssd1309 or sh1106")

        if col_offset is None:
            col_offset = 2 if self.controller == "sh1106" else 0
        self.col_offset = col_offset
        self._cmd = bytearray(2)
        self._cmd[0] = 0x80
        self._data_prefix = b'\x40'
        self._write_list = [self._data_prefix, None]
        self._writevto = getattr(i2c, "writevto", None)

        # **buffer**: use the supplied buffer or allocate a bytearray
        size = self.pages * self.width
        if buffer is None:
            self.buffer = bytearray(size)
        else:
            if len(buffer) != size:
                raise ValueError("Buffer length must be %d" % size)
            self.buffer = buffer

        # initialize FrameBuffer drawing primitives
        super().__init__(self.buffer, width, height, framebuf.MONO_VLSB)

        # initialize the display after setting up FrameBuffer
        self.init_display()

    def write_cmd(self, cmd):
        # prefix 0x80 = Co=1, D/C#=0
        self._cmd[1] = cmd
        self.i2c.writeto(self.addr, self._cmd)

    def write_data(self, buf):
        # prefix 0x40 = Co=0, D/C#=1
        if self._writevto is not None:
            self._write_list[1] = buf
            self._writevto(self.addr, self._write_list)
        else:
            self.i2c.writeto(self.addr, self._data_prefix + buf)

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,        # display off
            SET_MEM_ADDR, 0x00,     # horizontal addressing
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08,
            SET_DISP_OFFSET, 0x00,
            # controller-specific configuration:
            SET_COM_PIN_CFG, 0x12 if self.height == 64 else 0x02,
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0xF1,
            SET_VCOM_DESEL, 0x30,
            SET_CONTRAST, 0xFF,
            SET_ENTIRE_ON,
            SET_NORM_INV,
            SET_CHARGE_PUMP, 0x14,
            SET_DISP | 0x01        # display on
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def show(self):
        try:
            # **render the buffer** page by page
            col = self.col_offset
            lower_col = 0x00 | (col & 0x0F)
            higher_col = 0x10 | ((col >> 4) & 0x0F)

            for page in range(self.pages):
                # select the destination page
                self.write_cmd(0xB0 + page)  # SET_PAGE_ADDR  (0xB0..0xB7)
                self.write_cmd(lower_col)
                self.write_cmd(higher_col)

                start = page * self.width
                end   = start + self.width
                # write one row of data
                self.write_data(self.buffer[start:end])

            self.last_error = None
            return True
        except OSError as err:
            print("OLED display communication error:", err)
            self.last_error = err
            return False
