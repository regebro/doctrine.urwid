# -*- coding: UTF-8 -*-
import urwid

from encodings import codecs
from urwid.util import (move_prev_char, move_next_char,
                        is_wide_char)
from urwid.compat import bytes, PYTHON3

from doctrine.urwid.layout import CodeLayout

ONECHAR_NEWLINES = (u'\n', b'\n', u'\r', b'\r')
ERASE_LEFT = 'erase left'
ERASE_RIGHT = 'erase right'


class LineNosWidget(urwid.WidgetWrap):

    def render(self, size, focus=False):
        last_line = len(self._w.body.code.lines)
        width = max(3, len(str(last_line)))

        max_col, max_rows = size
        middle, top, bottom = self._w.calculate_visible(
            (max_col - width, max_rows), focus)

        lines = list(reversed(top[1:][0])) + [middle[1:-1]] + bottom[1:][0]
        widgets = [(line[2], LineNoWidget(line[1], line[2])) for line in lines]

        linenos = urwid.Pile(widgets)
        wrapper = urwid.Columns([(width, linenos), self._w], dividechars=1,
                                focus_column=1, box_columns=0)

        canv = wrapper.render(size, focus=focus)
        return canv


class LineNoWidget(urwid.Widget):
    _selectable = False
    _sizing = frozenset([urwid.FIXED])

    def __init__(self, row, rows):
        self.row = row
        self.rows = rows

    def render(self, size, focus=False):
        maxcol, maxrow = size
        code = '%%%ii' % maxcol
        text = [b''] * maxrow
        text[0] = (code % self.row).encode()
        attr = [(('lineno', maxcol),)] * maxrow
        return urwid.TextCanvas(text=text,
                                attr=attr,
                                maxcol=maxcol)


class LineEdit(urwid.Edit):
    def __init__(self, edit_text="", align=urwid.widget.LEFT,
                 wrap=urwid.widget.SPACE, layout=None, newline=None):

        self.newline = newline
        urwid.Edit.__init__(self, edit_text=edit_text, allow_tab=True,
                            align=align, wrap=wrap, layout=layout)
        self._wrap_mode = 'space'

    def get_edit_len(self):
        l = len(self._edit_text)
        while l and self._edit_text[l-1] in ONECHAR_NEWLINES:
            l -= 1
        return l

    def set_edit_pos(self, pos):
        l = self.get_edit_len()
        if pos > l:
            pos = l
        self.highlight = None
        self.pref_col_maxcol = None, None
        self._edit_pos = pos
        self._invalidate()

    def move_cursor_to_coords(self, size, x, y):
        (maxcol,) = size
        trans = self.get_line_translation(maxcol)
        top_x, top_y = self.position_coords(maxcol, 0)
        if y < top_y or y >= len(trans):
            return False

        pos = urwid.text_layout.calc_pos(self.get_text()[0], trans, x, y)
        e_pos = pos - len(self.caption)
        self.edit_pos = e_pos
        self.pref_col_maxcol = x, maxcol
        self._invalidate()
        return True

    def get_text(self):
        # We have a line, now make it into widgets:
        text = self._edit_text

        # Show the newline
        if text and text[-1] in '\r\n':
            text = text.rstrip('\r\n') + self.newline
        return text, self._attrib


class LineWalker(urwid.ListWalker):
    """ListWalker-compatible class for lazily reading file contents."""

    def __init__(self, code, newline, layout):
        self.code = code
        self.newline = newline
        self.focus = 0
        self.layout = layout
        self.widgets = []

    def _make_widget(self, edit_text):
        return LineEdit(edit_text, newline=self.newline, layout=self.layout)

    def get_focus(self):
        return self._get_at_pos(self.focus)

    def set_focus(self, focus):
        self.focus = focus
        self._modified()

    def get_next(self, start_from):
        return self._get_at_pos(start_from + 1)

    def get_prev(self, start_from):
        return self._get_at_pos(start_from - 1)

    def _get_at_pos(self, pos):
        """Return a widget for the line number passed."""

        if pos < 0:
            # line 0 is the start of the file, no more above
            return None, None

        l = len(self.widgets)
        if pos < l:
            # we have that line so return it
            return self.widgets[pos], pos

        # Fetch the line
        try:
            next_line = self.code[pos]
        except IndexError:
            # Past end of file:
            return None, None

        edit = self._make_widget(next_line)
        edit.set_edit_pos(0)
        self.widgets.append(edit)

        return edit, pos

    def split_focus(self, insertion):
        """The focus line has been split into two"""
        pos = self.focus
        focus_widget = self.widgets[pos]
        col = focus_widget.edit_pos
        self.code.split_row(pos, col, insertion)
        self.widgets[pos].set_edit_text(self.code[pos])
        new_widget = self._make_widget(self.code[pos + 1])
        new_widget.set_edit_pos(0)
        self.widgets.insert(self.focus + 1, new_widget)
        self.set_focus(pos + 1)

    def combine_focus_with_prev(self):
        """Combine the focus edit widget with the one above."""
        focus_widget, pos = self.get_prev(self.focus)
        focus_widget.set_edit_pos(focus_widget.get_edit_len())
        self.code.merge_rows(pos, pos + 1)
        focus_widget.set_edit_text(self.code[pos])
        del self.widgets[pos + 1]
        self.focus = pos

    def combine_focus_with_next(self):
        """Combine the focus edit widget with the one below."""
        pos = self.focus
        focus_widget, ignore = self.get_next(pos)
        self.code.merge_rows(pos, pos + 1)
        focus_widget.set_edit_text(self.code[pos])
        focus_widget.set_edit_pos(self.widgets[pos].edit_pos)
        del self.widgets[pos]


class EditorConfig(object):
    newline = u'↲'
    screen_encoding = 'UTF-8'
    command_map = {
        'backspace': ERASE_LEFT,
        'delete': ERASE_RIGHT,
    }

    def __init__(self, **kw):
        self.__dict__.update(kw)


class TextEditor(urwid.ListBox):
    _sizing = frozenset(['box'])

    def __init__(self, file, config):
        """An Urwid code editor widget.

        file: A file like object.
        config: An EditorConfig object.
        """
        walker = LineWalker(file, newline=config.newline,
                            layout=CodeLayout())
        self.parser = None
        urwid.ListBox.__init__(self, walker)
        self.config = config
        self.codec = codecs.getencoder(config.screen_encoding)
        for k, v in self.config.command_map.items():
            self._command_map[k] = v

    def valid_char(self, ch):
        """
        Filter for text that may be entered into this widget by the user

        :param ch: character to be inserted
        :type ch: bytes or unicode

        This implementation returns True for all printable characters.
        """
        return is_wide_char(ch, 0) or (len(ch) == 1 and ord(ch) >= 32)

    def insert_text(self, key, focus_widget, pos):
        col = focus_widget.edit_pos
        text = self.body.code[pos]
        text = text[:col] + key + text[col:]
        self.body.code[pos] = text
        focus_widget.set_edit_text(text)
        focus_widget.set_edit_pos(col + 1)

    def keypress(self, size, key):
        (maxcol, maxrow) = size

        focus_widget, pos = self.body.get_focus()

        # This is copied. I don't understand what it does.
        # I will test to remove it, but later.
        def actual_key(unhandled):
            if unhandled:
                return key

        if self.valid_char(key):
            self.insert_text(key, focus_widget, pos)
            return

        if self.set_focus_pending or self.set_focus_valign_pending:
            self._set_focus_complete((maxcol, maxrow), focus=True)

        if key == "tab":
            # Tab is magical and maps to different commands in different
            # situations. So far we insert a tab, though.
            self.insert_text('\t', focus_widget, pos)
            return

        if key == "enter":
            # We don't want to be able to remap enter, so we handle it here,
            # shortcutting it's command mapping.
            self.body.split_focus('\n')
            return

        command = self._command_map[key]
        # pass off the heavy lifting
        if command == urwid.CURSOR_UP:
            return actual_key(self._keypress_up((maxcol, maxrow)))

        if command == urwid.CURSOR_DOWN:
            return actual_key(self._keypress_down((maxcol, maxrow)))

        if command == urwid.CURSOR_PAGE_UP:
            return actual_key(self._keypress_page_up((maxcol, maxrow)))

        if command == urwid.CURSOR_PAGE_DOWN:
            return actual_key(self._keypress_page_down((maxcol, maxrow)))

        if command == urwid.CURSOR_MAX_LEFT:
            focus_widget.set_edit_pos(0)
            return

        if command == urwid.CURSOR_MAX_RIGHT:
            focus_widget.set_edit_pos(focus_widget.get_edit_len())
            return

        if command == urwid.CURSOR_LEFT:
            col = focus_widget.edit_pos
            if col != 0:
                col = move_prev_char(focus_widget.edit_text, 0, col)
                focus_widget.set_edit_pos(col)
                return

            # Start of line, move to previous line, if any:
            if self.focus_position == 0:
                # No previous line
                return key

            focus_widget, pos = self.body.get_prev(pos)
            self.set_focus(pos, 'below')
            self.keypress(size, "end")
            return

        if command == urwid.CURSOR_RIGHT:
            col = focus_widget.edit_pos
            l = focus_widget.get_edit_len()
            if col < l:
                col = move_next_char(focus_widget.edit_text, col,
                                     len(focus_widget.edit_text))
                focus_widget.set_edit_pos(col)
                return

            # We are moving beyond the end of line, go to next line.
            focus_widget, pos = self.body.get_next(pos)
            if not focus_widget:
                # No more lines
                return key

            self.set_focus(pos, 'above')
            self.keypress(size, "home")
            return

        if command == ERASE_LEFT:
            col = focus_widget.edit_pos
            if col == 0:
                if pos == 0:
                    # Nothing to delete
                    return key
                # Merge the lines
                self.body.combine_focus_with_prev()
                return
            self.body.code.delete_characters(pos, col-1, pos, col)
            focus_widget.set_edit_text(self.body.code[pos])
            focus_widget.set_edit_pos(col-1)
            return

        if command == ERASE_RIGHT:
            col = focus_widget.edit_pos
            if col == focus_widget.get_edit_len():
                # End of line
                nextline, ignore = self.body.get_next(pos)
                if nextline is None:
                    # Nothing to delete
                    return key
                # Merge the lines
                self.body.combine_focus_with_next()
                return
            self.body.code.delete_characters(pos, col, pos, col + 1)
            focus_widget.set_edit_text(self.body.code[pos])
            return

        return key
