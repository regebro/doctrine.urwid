# -*- coding: UTF-8 -*-
import urwid
import math

from encodings import codecs
from urwid.util import move_prev_char, move_next_char, calc_width, calc_text_pos, is_wide_char
from urwid.text_layout import CanNotDisplayText, TextLayout, line_width
from urwid.compat import bytes, PYTHON3, B


if PYTHON3:
    STRING_TYPES = (bytes, str)  # pragma: no cover
else:
    STRING_TYPES = (str, unicode)  # pragma: no cover

TWOCHAR_NEWLINES = (u'\n\r', b'\n\r', u'\r\n', b'\r\n')
ONECHAR_NEWLINES = (u'\n', b'\n', u'\r', b'\r')

def find_newline(text, pos):
    l = len(text)
    while pos < l:
        char = text[pos:pos+1]

        if char in ONECHAR_NEWLINES:
            return pos
        pos += 1

    return pos


class CodeLayout(TextLayout):

    tab_width = 8

    def supports_align_mode(self, align):
        """Return True if align is a supported align mode."""
        return align == urwid.LEFT

    def supports_wrap_mode(self, wrap):
        """Return True if wrap is a supported wrap mode."""
        return wrap == urwid.SPACE

    def layout(self, text, width, align, wrap ):
        """Return a layout structure for text."""
        try:
            segs = self.calculate_text_segments(text, width, wrap)
            return self.align_layout(text, width, segs, wrap, align)
        except CanNotDisplayText:
            return [[]]

    def calculate_text_segments(self, text, width, wrap):
        """
        Calculate the segments of text to display given width screen
        columns to display them.

        text - unicode text or byte string to display
        width - number of available screen columns
        wrap - wrapping mode used

        Returns a layout structure without alignment applied.
        """

        # TODO: This function is a horror and a mess, and really hard to
        # understand. It's based on urwids StandardLayout, which by itself
        # is overly complex, and I added tab handling, which made it worse.
        # It's a prime candidate for refacturing, making easier to understand
        # and as it is heavily used, profiling would be nice too.

        nl, nl_o, sp_o, tab_o = "\n", "\n", " ", "\t"
        if PYTHON3 and isinstance(text, bytes):
            nl = B(nl) # can only find bytes in python3 bytestrings
            nl_o = ord(nl_o) # + an item of a bytestring is the ordinal value
            sp_o = ord(sp_o)
            tab_o = ord(tab_o)
        b = []
        p = 0
        if wrap == 'clip':
            # no wrapping to calculate, so it's easy.
            l = []
            while p<=len(text):
                n_cr = find_newline(text, p)
                if p != n_cr:
                    line = text[p:n_cr]
                    pt = 0
                    while pt < len(line):
                        n_tab = line.find(tab_o, pt)
                        if n_tab == -1:
                            end = len(line)
                        else:
                            end = n_tab

                        sc = calc_width(line, pt, end)
                        if sc != 0:
                            l.append((sc, p + pt, p + end))

                        if end == n_tab: # A tab was found
                            extra_space = self.tab_width - (sc % self.tab_width)
                            l.append((extra_space, p + n_tab))

                        pt = end + 1

                l.append((0, n_cr))
                b.append(l)
                l = []
                if text[n_cr:n_cr+2] in TWOCHAR_NEWLINES:
                    # Two char newline:
                    p = n_cr + 2
                else:
                    p = n_cr + 1
            return b

        while p <= len(text):
            # look for next eligible line break
            n_cr = find_newline(text, p)

            line = text[p:n_cr]
            l = []
            pt = 0
            lc = 0
            while pt < len(line):
                n_tab = line.find(tab_o, pt)
                if n_tab == -1:
                    end = len(line)
                else:
                    end = n_tab

                sc = calc_width(line, pt, end)

                if lc + sc <= width:
                    # this segment fits
                    if sc:
                        l.append((sc, p + pt, p + end))
                    if end == n_tab: # A tab was found
                        extra_space = self.tab_width - (sc % self.tab_width)
                        l.append((extra_space, p + n_tab))
                        lc += extra_space
                    else:
                        # removed character hint
                        l.append((0, p + end))

                    pt = end + 1
                    lc += sc

                    if lc >= width:
                        # The tab can sometimes push line length to width,
                        # and then we adjust the line length and make a new line.
                        overshoot = lc - width
                        spaces, pos = l[-1]
                        l[-1] = (spaces - overshoot, pos)
                        b.append(l)
                        l = []
                        lc = 0
                    continue

                # This segment does not fit. Let's fit it.
                pos, sc = calc_text_pos(line, pt, end, width - lc)
                if pos == pt: # pathological width=1 double-byte case
                    raise CanNotDisplayText(
                        "Wide character will not fit in 1-column width")

                if wrap == 'any':
                    l.append((sc, p + pt, p + pos))
                    l.append((0, p + pos))
                    b.append(l)
                    l = []
                    lc = 0
                    pt = pos
                    continue

                assert wrap == 'space'
                if line[pos] == sp_o:
                    # perfect space wrap
                    l.append((sc, p + pt, p + pos))
                    # removed character hint
                    l.append((0, p + pos))
                    b.append(l)
                    l = []
                    lc = 0
                    pt = pos + 1
                    continue

                if is_wide_char(line, pos):
                    # perfect next wide
                    l.append((sc, p + pt, p + pos))
                    b.append(l)
                    l = []
                    lc = 0
                    pt = pos
                    continue

                prev = pos
                while prev > pt:
                    prev = move_prev_char(line, pt, prev)
                    if line[prev] == sp_o:
                        sc = calc_width(line, pt, prev)
                        if prev != pt:
                            l.append((sc, p + pt, p + prev))
                        l.append((0, p + prev))
                        b.append(l)
                        l = []
                        lc = 0
                        pt = prev + 1
                        break

                    if is_wide_char(line, prev):
                        # wrap after wide char
                        nextc = move_next_char(line, prev, pos)
                        sc = calc_width(line, pt, nextc)
                        l.append((sc, p + pt, p + nextc))
                        b.append(l)
                        l = []
                        lc = 0
                        pt = nextc
                        break
                else:
                    if lc == 0:
                        # unwrap previous line space if possible to
                        # fit more text (we're breaking a word anyway)
                        if b and (len(b[-1]) == 2 or ( len(b[-1])==1
                                and len(b[-1][0])==2 )):
                            # look for removed space above
                            if len(b[-1]) == 1:
                                [(h_sc, h_off)] = b[-1]
                                p_sc = 0
                                p_off = p_end = h_off
                            else:
                                [(p_sc, p_off, p_end),
                                 (h_sc, h_off)] = b[-1][-2:]
                            if (p_sc < width and h_sc==0 and
                                text[h_off] == sp_o):
                                # combine with previous line
                                old_line = b[-1][:-2]
                                del b[-1]
                                pt = p_off - p
                                pos, sc = calc_text_pos(
                                    line, pt, end, width )
                                old_line.append((sc, p + pt, p + pos))
                                b.append(old_line)
                                # check for trailing " " or "\n"
                                pt = pos
                                if pt < len(text) and (
                                    text[pt] in (sp_o, nl_o)):
                                    # removed character hint
                                    b[-1].append((0, p + pt))
                                    pt += 1
                                continue
                    # Break on previous tab, and try again.
                    if l:
                        b.append(l)
                        l = []
                        lc = 0
                        continue

                    # There is no space to break the line on, unwrapping the
                    # previous line doesn't help, I guess we just break on a
                    # character.
                    b.append([(sc, p + pt, p + pos)])
                    l = []
                    lc = 0
                    pt = pos

            # force any char wrap
            if l:
                b.append(l)
            elif not line:
                # An empty line.
                b.append([(0, n_cr)])
                pt = 1

            if text[pt-1:pt+1] in TWOCHAR_NEWLINES:
                # Two char newline:
                pt += 1
            p += pt
        return b

    def align_layout( self, text, width, segs, wrap, align ):
        """Convert the layout segs to an aligned layout."""
        assert align==urwid.LEFT
        return segs


class LineNosWidget(urwid.WidgetWrap):

    def render(self, size, focus=False):
        last_line = len(self._w.walker.code.lines)
        width = max(3, len(str(last_line)))

        max_col, max_rows = size
        middle, top, bottom = self._w.calculate_visible((max_col - width, max_rows), focus)

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

    def _edit_len(self):
        l = len(self._edit_text)
        while l and self._edit_text[l-1] in ONECHAR_NEWLINES:
            l -= 1
        return l

    def set_edit_pos(self, pos):
        l = self._edit_len()
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

        pos = urwid.text_layout.calc_pos( self.get_text()[0], trans, x, y )
        e_pos = pos - len(self.caption)
        l = self._edit_len()
        if e_pos > l:
            e_pos = l
        self.edit_pos = e_pos
        self.pref_col_maxcol = x, maxcol
        self._invalidate()
        return True

    def keypress(self, size, key):
        p = self.edit_pos

        if key=="tab" and self.allow_tab:
            self.insert_text('\t')

        elif self._command_map[key] == urwid.CURSOR_LEFT:
            if p==0:
                return key
            p = move_prev_char(self.edit_text,0,p)
            self.set_edit_pos(p)

        elif self._command_map[key] == urwid.CURSOR_RIGHT:
            l = self._edit_len()
            if self.edit_pos >= l:
                return key
            p = move_next_char(self.edit_text,p,len(self.edit_text))
            # Expand the tabs:
            self.set_edit_pos(p)

        else:
            return urwid.Edit.keypress(self, size, key)

    def get_text(self):
        # We have a line, now make it into widgets:
        text = self._edit_text

        # Show the newline
        if text[-1:] in '\r\n':
            text = text.rstrip('\r\n') + self.newline
        return text, self._attrib


class LineWalker(urwid.ListWalker):
    """ListWalker-compatible class for lazily reading file contents."""

    def __init__(self, code, newline, layout):
        self.code = code
        self.newline = newline
        self.focus = 0
        self.layout = layout
        self.widgets = {}

    def get_focus(self):
        return self._get_at_pos(self.focus)

    def set_focus(self, focus):
        self.focus = focus
        self._modified()

    def get_next(self, start_from):
        return self._get_at_pos(start_from + 1)

    def get_prev(self, start_from):
        return self._get_at_pos(start_from - 1)

    def read_next_line(self):
        """Read another line from the file."""

        next_line = self.file.readline()

        if not next_line or next_line[-1:] != '\n':
            # no newline on last line of file
            self.file = None
        else:
            # trim newline characters
            next_line = next_line[:-1]

    def _get_at_pos(self, pos):
        """Return a widget for the line number passed."""

        if pos < 0:
            # line 0 is the start of the file, no more above
            return None, None

        if pos in self.widgets:
            # we have that line so return it
            return self.widgets[pos], pos

        # Fetch the line
        try:
            next_line = self.code[pos]
        except IndexError:
            # Past end of file:
            return None, None

        edit = LineEdit(next_line, newline=self.newline, layout=self.layout)
        edit.set_edit_pos(0)
        self.widgets[pos] = edit

        return edit, pos

    def split_focus(self):
        """Divide the focus edit widget at the cursor location."""

        focus = self.lines[self.focus]
        pos = focus.edit_pos
        edit = LineEdit(focus.edit_text[pos:], allow_tab=True)
        focus.set_edit_text(focus.edit_text[:pos])
        edit.set_edit_pos(0)
        self.lines.insert(self.focus+1, edit)

    def combine_focus_with_prev(self):
        """Combine the focus edit widget with the one above."""

        above, ignore = self.get_prev(self.focus)
        if above is None:
            # already at the top
            return

        focus = self.lines[self.focus]
        above.set_edit_pos(len(above.edit_text))
        above.set_edit_text(above.edit_text + focus.edit_text)
        del self.lines[self.focus]
        self.focus -= 1

    def combine_focus_with_next(self):
        """Combine the focus edit widget with the one below."""

        below, ignore = self.get_next(self.focus)
        if below is None:
            # already at bottom
            return

        focus = self.lines[self.focus]
        focus.set_edit_text(focus.edit_text + below.edit_text)
        del self.lines[self.focus+1]


class EditorConfig(object):
    newline = u'↲'
    screen_encoding = 'UTF-8'

    def __init__(self, **kw):
        self.__dict__.update(kw)


class TextEditor(urwid.ListBox):
    _sizing = frozenset(['box'])

    def __init__(self, file, config):
        """An Urwid code editor widget.

        file: A file like object.
        config: An EditorConfig object.
        """
        self.walker = LineWalker(file, newline=config.newline,
                                 layout=CodeLayout())
        self.parser = None
        urwid.ListBox.__init__(self, self.walker)
        self.config = config
        self.codec = codecs.getencoder(config.screen_encoding)

    def selectable(self):
        return True

    def keypress(self, size, key):
        key = urwid.ListBox.keypress(self, size, key)
        if key is None:
            return  # Key was handled

        # Unhandled keys
        if self._command_map[key] == urwid.CURSOR_LEFT:
            if self.focus_position == 0:
                return key
            w, pos = self.walker.get_focus()
            w, pos = self.walker.get_prev(pos)
            if w:
                self.set_focus(pos, 'below')
                self.keypress(size, "end")
        elif self._command_map[key] == urwid.CURSOR_RIGHT:
                w, pos = self.walker.get_focus()
                w, pos = self.walker.get_next(pos)
                if w:
                    self.set_focus(pos, 'above')
                    self.keypress(size, "home")
