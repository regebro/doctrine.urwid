# -*- coding: UTF-8 -*-
import urwid

from urwid.util import (move_prev_char, move_next_char, calc_width,
                        calc_text_pos, is_wide_char)
from urwid.text_layout import CanNotDisplayText, TextLayout
from urwid.compat import bytes, PYTHON3, B

ONECHAR_NEWLINES = (u'\n', b'\n', u'\r', b'\r')
TWOCHAR_NEWLINES = (u'\n\r', b'\n\r', u'\r\n', b'\r\n')


def find_newline(text, pos):
    l = len(text)
    while pos < l:
        char = text[pos:pos+1]

        if char in ONECHAR_NEWLINES:
            return pos
        pos += 1

    return pos


class CodeLayout(TextLayout):
    """A layout for Urwid that can deal with tabs."""

    tab_width = 8

    def supports_align_mode(self, align):
        """Return True if align is a supported align mode."""
        return align == urwid.LEFT

    def supports_wrap_mode(self, wrap):
        """Return True if wrap is a supported wrap mode."""
        return wrap == urwid.SPACE

    def layout(self, text, width, align, wrap):
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
            nl = B(nl)  # can only find bytes in python3 bytestrings
            nl_o = ord(nl_o)  # + an item of a bytestring is the ordinal value
            sp_o = ord(sp_o)
            tab_o = ord(tab_o)
        b = []
        p = 0
        if wrap == 'clip':
            # no wrapping to calculate, so it's easy.
            l = []
            while p <= len(text):
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

                        if end == n_tab:  # A tab was found
                            extra_space = (self.tab_width - (
                                sc % self.tab_width))
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
                    if end == n_tab:  # A tab was found
                        extra_space = self.tab_width - (sc % self.tab_width)
                        l.append((extra_space, p + n_tab))
                        lc += extra_space
                    else:
                        # removed character hint
                        l.append((0, p + end))

                    pt = end + 1
                    lc += sc

                    if lc >= width:
                        # The tab can sometimes push line length to width, and
                        # then we adjust the line length and make a new line.
                        overshoot = lc - width
                        spaces, pos = l[-1]
                        l[-1] = (spaces - overshoot, pos)
                        b.append(l)
                        l = []
                        lc = 0
                    continue

                # This segment does not fit. Let's fit it.
                pos, sc = calc_text_pos(line, pt, end, width - lc)
                if pos == pt:  # pathological width=1 double-byte case
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
                        if b and (len(b[-1]) == 2 or (len(b[-1]) == 1 and
                                                      len(b[-1][0]) == 2)):
                            # look for removed space above
                            if len(b[-1]) == 1:
                                [(h_sc, h_off)] = b[-1]
                                p_sc = 0
                                p_off = p_end = h_off
                            else:
                                [(p_sc, p_off, p_end),
                                 (h_sc, h_off)] = b[-1][-2:]
                            if (p_sc < width and h_sc == 0 and
                               text[h_off] == sp_o):
                                # combine with previous line
                                old_line = b[-1][:-2]
                                del b[-1]
                                pt = p_off - p
                                pos, sc = calc_text_pos(
                                    line, pt, end, width)
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

    def align_layout(self, text, width, segs, wrap, align):
        """Convert the layout segs to an aligned layout."""
        assert align == urwid.LEFT
        return segs
