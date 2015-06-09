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
or sem."""


class TextEditorTest(unittest.TestCase):

    def _get_editor(self, text):
        # Need to have an ascii character for this, as we don't have a
        # terminal during the tests, and encoding defaults to ascii.
        config = urwid.EditorConfig(newline='*')
        codeob = code.Code(io.StringIO(text))
        return urwid.TextEditor(codeob, config)

    def test_linenumbers(self):
        editor = self._get_editor(LOREM)
        line_widget = urwid.LineNosWidget(editor)
        result = line_widget.render((70, 25))
        self.assertEqual(result.text[0][:4], b'  0 ')
        self.assertEqual(result.text[1][:4], b'  1 ')
        # Second line wraps, so no number on line 3:
        self.assertEqual(result.text[2][:4], b'    ')

    def test_render_small(self):
        widget = self._get_editor(u'A text\nwith several\nlines')
        result = widget.render((15, 15))
        self.assertEqual(result.text[0], b'A text*        ')

    def test_render_empty(self):
        widget = self._get_editor(u'')
        size = (80, 25)

        canvas = widget.render(size)
        self.assertEqual(canvas.text[0], 80 * ' ')
        self.assertEqual(widget.keypress(size, 'backspace'), 'backspace')
        self.assertEqual(widget.keypress(size, 'delete'), 'delete')
        self.assertIsNone(widget.keypress(size, 'enter'))
        self.assertEqual(widget.body.code[0], '\n')
        self.assertEqual(widget.body.code[1], '')

    def test_movement(self):
        widget = self._get_editor(LOREM)
        size = (80, 24)

        # We start at 0, 0
        self.assertEqual(widget.get_cursor_coords(size), (0, 0))
        # Down moves to next line
        widget.keypress(size, 'down')
        self.assertEqual(widget.get_cursor_coords(size), (0, 1))
        # And right moves a character in
        widget.keypress(size, 'right')
        self.assertEqual(widget.get_cursor_coords(size), (1, 1))
        # And left moves a character back
        widget.keypress(size, 'left')
        self.assertEqual(widget.get_cursor_coords(size), (0, 1))
        # Note that focus_position is which row we are editing,
        # While cursor_coords are where the cursor are on the screen
        # At this point they are the same
        self.assertEqual(widget.focus_position, 1)
        # But now we page down
        widget.keypress(size, 'page down')
        # It moved the cursor to the last line:
        self.assertEqual(widget.get_cursor_coords(size), (0, 23))
        # But we are editing one page down, ie 1 + 24, so now
        # edit row and cursor coords are not the same any more.
        self.assertEqual(widget.focus_position, 25)
        # Page up moves to top of screen
        widget.keypress(size, 'page up')
        self.assertEqual(widget.get_cursor_coords(size), (0, 0))
        # But, back to line 1!
        self.assertEqual(widget.focus_position, 1)
        # Move beyond start of line moves one line up
        widget.keypress(size, 'left')
        self.assertEqual(widget.get_cursor_coords(size), (63, 0))
        self.assertEqual(widget.focus_position, 0)
        # Home goes to the start of the line
        widget.keypress(size, 'home')
        self.assertEqual(widget.get_cursor_coords(size), (0, 0))
        # We are no back at the start of file, and can't go left
        widget.keypress(size, 'left')
        self.assertEqual(widget.get_cursor_coords(size), (0, 0))
        # Go to the end of the line
        widget.keypress(size, 'end')
        self.assertEqual(widget.get_cursor_coords(size), (63, 0))
        # Move beyond end of line, goes to start of next line
        widget.keypress(size, 'right')
        self.assertEqual(widget.get_cursor_coords(size), (0, 1))

    def test_movement_limits(self):
        widget = self._get_editor(LOREM)
        size = (80, 24)
        self.assertEqual(widget.get_cursor_coords(size), (0, 0))
        widget.keypress(size, 'up')
        self.assertEqual(widget.get_cursor_coords(size), (0, 0))
        widget.keypress(size, 'left')
        self.assertEqual(widget.get_cursor_coords(size), (0, 0))
        widget.keypress(size, 'page down')
        self.assertEqual(widget.get_cursor_coords(size), (0, 23))
        widget.keypress(size, 'page down')
        self.assertEqual(widget.get_cursor_coords(size), (0, 23))
        widget.keypress(size, 'end')
        self.assertEqual(widget.get_cursor_coords(size), (7, 23))
        widget.keypress(size, 'right')
        self.assertEqual(widget.get_cursor_coords(size), (7, 23))

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

    def test_delete(self):
        widget = self._get_editor(u'A text\nwith several\nlines')
        size = (80, 25)
        widget.keypress(size, 'page down')
        widget.keypress(size, 'end')
        widget.keypress(size, 'delete')
        self.assertEqual(widget.get_cursor_coords(size), (5, 2))
        self.assertEqual(widget.body.code[2], u'lines')
        widget.keypress(size, 'left')
        self.assertEqual(widget.get_cursor_coords(size), (4, 2))
        widget.keypress(size, 'delete')
        self.assertEqual(widget.get_cursor_coords(size), (4, 2))
        self.assertEqual(widget.body.code[2], u'line')
        widget.keypress(size, 'up')
        widget.keypress(size, 'end')
        self.assertEqual(widget.get_cursor_coords(size), (12, 1))
        widget.keypress(size, 'delete')
        self.assertEqual(widget.get_cursor_coords(size), (12, 1))
        self.assertEqual(widget.body.code[1], u'with severalline')
        self.assertEqual(len(widget.body.code), 2)

    def test_backspace(self):
        widget = self._get_editor(u'A text\nwith several\nlines')
        size = (80, 25)
        widget.keypress(size, 'backspace')
        self.assertEqual(widget.get_cursor_coords(size), (0, 0))
        self.assertEqual(widget.body.code[0], u'A text\n')
        widget.keypress(size, 'right')
        self.assertEqual(widget.get_cursor_coords(size), (1, 0))
        widget.keypress(size, 'backspace')
        self.assertEqual(widget.get_cursor_coords(size), (0, 0))
        self.assertEqual(widget.body.code[0], u' text\n')
        widget.keypress(size, 'down')
        widget.keypress(size, 'backspace')
        self.assertEqual(widget.get_cursor_coords(size), (5, 0))
        self.assertEqual(widget.body.code[0], u' textwith several\n')
        self.assertEqual(len(widget.body.code), 2)

    def test_inserts(self):
        widget = self._get_editor(u'A text\nwith several\nlines')
        size = (80, 25)
        widget.keypress(size, 'right')
        widget.keypress(size, 'right')
        widget.keypress(size, '!')
        widget.keypress(size, 'right')
        widget.keypress(size, 'right')
        self.assertEqual(widget.get_cursor_coords(size), (5, 0))
        widget.keypress(size, 'tab')
        self.assertEqual(widget.get_cursor_coords(size), (8, 0))
        widget.keypress(size, 'tab')
        self.assertEqual(widget.get_cursor_coords(size), (16, 0))
        self.assertEqual(widget.body.code[0], u'A !te\t\txt\n')
        widget.keypress(size, 'enter')
        self.assertEqual(widget.body.code[0], u'A !te\t\t\n')
        self.assertEqual(widget.body.code[1], u'xt\n')

    def test_keypress(self):
        widget = self._get_editor(u'A text\nwith several\nlines')
        size = (80, 25)
        # Unhandled keys should be returned
        self.assertEqual(widget.keypress(size, 'left'), 'left')
        self.assertEqual(widget.keypress(size, 'F4'), 'F4')

        # Others not
        self.assertIsNone(widget.keypress(size, 'right'))
        self.assertIsNone(widget.keypress(size, 'delete'))
        self.assertIsNone(widget.keypress(size, 'r'))
        self.assertIsNone(widget.keypress(size, 'enter'))
