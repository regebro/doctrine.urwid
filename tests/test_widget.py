# -*- coding: UTF-8 -*-
import io
import unittest
from doctrine import urwid
from doctrine import code

LOREM = u"""Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed in
semper nisi, elementum elementum nibh. Aliquam malesuada purus nec ante
aliquam, ac placerat tellus volutpat. Suspendisse efficitur convallis magna eu
euismod. Donec mattis laoreet libero, et consequat sem vehicula in.
Suspendisse auctor tortor enim, eu blandit tortor convallis id. Sed in
consectetur odio, id semper eros. Nam consectetur nibh vel sem interdum
dictum. Sed lobortis massa bibendum purus euismod maximus. Fusce mollis,
nibh in suscipit rhoncus, lectus quam porttitor lectus, sed aliquet odio augue
tempor libero. Aliquam faucibus id ante non aliquam. Quisque eu neque nec est
molestie porta. Vestibulum ante ipsum primis in faucibus orci luctus et
ultrices posuere cubilia Curae; Interdum et malesuada fames ac ante ipsum
primis in faucibus.

Sed quis vehicula nunc. Praesent tincidunt elementum pharetra. Nullam dui
erat, malesuada et maximus vel, venenatis tincidunt sem. Suspendisse potenti.
Phasellus sodales sapien sed aliquet suscipit. Fusce at ligula mollis lectus
sollicitudin pretium. Quisque tempus ac nisl et facilisis.

Fusce finibus, nulla eu scelerisque pharetra, nibh turpis condimentum arcu, ac
viverra neque massa nec magna. Pellentesque id ultrices orci. Suspendisse ac
faucibus lorem, eu sollicitudin velit. Class aptent taciti sociosqu ad litora
torquent per conubia nostra, per inceptos himenaeos. Pellentesque habitant
morbi tristique senectus et netus et malesuada fames ac turpis egestas.
Phasellus pharetra nisl quis aliquet mattis. Phasellus et diam urna. In ac
tristique felis, vel ultrices eros. Donec nec mauris ut nisl ultrices iaculis
ac vitae erat. Cras varius pulvinar metus eu varius. Sed at magna lacus.
Aliquam id purus augue. Nulla facilisi.
or sem.
"""

class TextEditor(unittest.TestCase):

    def _get_editor(self, text):
        # Need to have an ascii character for this, as we don't have a
        # terminal during the tests, and encoding defaults to ascii.
        config = urwid.EditorConfig(newline='*')
        codeob = code.Code(io.StringIO(text))
        return urwid.TextEditor(codeob, config)

    def test_render_small(self):
        widget = self._get_editor(u'A text\nwith several\nlines')
        result = widget.render((15, 15))
        self.assertEqual(result.text[0], b'A text*        ')

    def test_movement(self):
        widget = self._get_editor(LOREM)
        size = (80, 24)
        self.assertEqual(widget.get_cursor_coords(size), (0, 0))
        widget.keypress(size, 'down')
        self.assertEqual(widget.get_cursor_coords(size), (0, 1))
        widget.keypress(size, 'right')
        self.assertEqual(widget.get_cursor_coords(size), (1, 1))
        widget.keypress(size, 'left')
        self.assertEqual(widget.get_cursor_coords(size), (0, 1))
        widget.keypress(size, 'page down')
        self.assertEqual(widget.get_cursor_coords(size), (0, 23))
        widget.keypress(size, 'page up')
        self.assertEqual(widget.get_cursor_coords(size), (0, 0))
        # Move beyond start of line
        widget.keypress(size, 'left')
        self.assertEqual(widget.get_cursor_coords(size), (64, 0))
        # Move beyond end of line
        widget.keypress(size, 'right')
        self.assertEqual(widget.get_cursor_coords(size), (0, 1))

    def test_tabs(self):
        widget = self._get_editor(u'A tab\tfor spacing checks\n\t\tcode\n')
        size = (80, 24)
        self.assertEqual(widget.get_cursor_coords(size), (0, 0))
        widget.keypress(size, 'down')
        self.assertEqual(widget.get_cursor_coords(size), (0, 1))

        # Now go right on a tab, and we should end up 8 characters in:
        widget.keypress(size, 'right')
        self.assertEqual(widget.get_cursor_coords(size), (8, 1))

        # Right again, and we are 16 characters in:
        widget.keypress(size, 'right')
        self.assertEqual(widget.get_cursor_coords(size), (16, 1))

        # Backspace and then right again, and we are 9 characters in:
        widget.keypress(size, 'backspace')
        widget.keypress(size, 'right')
        self.assertEqual(widget.get_cursor_coords(size), (9, 1))

    def test_backspace(self):
        widget = self._get_editor(u'A text\nwith several\nlines')
        widget.keypress((80, 25), 'backspace')
