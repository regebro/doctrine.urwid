# -*- coding: UTF-8 -*-
import unittest
import urwid

from urwid import text_layout
from urwid.compat import B
from doctrine.urwid import CodeLayout


##################################################
# Tests copied from urwid.tests.test_text_layout
##################################################

layout = CodeLayout()


class CalcBreaksTest(object):
    def cbtest(self, width, exp):
        result = layout.calculate_text_segments(
            B(self.text), width, self.mode)
        assert len(result) == len(exp), repr((result, exp))
        for l, e in zip(result, exp):
            end = l[-1][-1]
            assert end == e, repr((result, exp))

    def test(self):
        for width, exp in self.do:
            self.cbtest(width, exp)


class CalcTabTest(object):
    def cbtest(self, width, exp):
        result = layout.calculate_text_segments(
            B(self.text), width, self.mode)
        assert len(result) == len(exp), repr((result, exp))
        for l, e in zip(result, exp):
            assert len(l) == len(e), repr((result, exp))
            for ls, es in zip(l, e):
                end = ls[-1]
            assert end == es, repr((result, exp))

    def test(self):
        for width, exp in self.do:
            self.cbtest(width, exp)


class CalcBreaksCharTest(CalcBreaksTest, unittest.TestCase):
    mode = 'any'
    text = "abfghsdjf askhtrvs\naltjhgsdf ljahtshgf"
    # tests
    do = [
        (100, [18, 38]),
        (6, [6, 12, 18, 25, 31, 37, 38]),
        (10, [10, 18, 29, 38]),
    ]


class CalcBreaksDBCharTest(CalcBreaksTest, unittest.TestCase):
    def setUp(self):
        urwid.set_encoding("euc-jp")

    mode = 'any'
    text = "abfgh\xA1\xA1j\xA1\xA1xskhtrvs\naltjhgsdf\xA1\xA1jahtshgf"
    # tests
    do = [
        (10, [10, 18, 28, 38]),
        (6, [5, 11, 17, 18, 25, 31, 37, 38]),
        (100, [18, 38]),
    ]


class CalcBreaksWordTest(CalcBreaksTest, unittest.TestCase):
    mode = 'space'
    text = "hello world\nout there. blah"
    # tests
    do = [
        (10, [5, 11, 22, 27]),
        (5, [5, 11, 17, 22, 27]),
        (100, [11, 27]),
    ]


class CalcBreaksWordTest2(CalcBreaksTest, unittest.TestCase):
    mode = 'space'
    text = "A simple set of words, really...."
    do = [
        (10, [8, 15, 22, 33]),
        (17, [15, 33]),
        (13, [12, 22, 33]),
    ]


class CalcBreaksDBWordTest(CalcBreaksTest, unittest.TestCase):
    def setUp(self):
        urwid.set_encoding("euc-jp")

    mode = 'space'
    text = "hel\xA1\xA1 world\nout-\xA1\xA1tre blah"
    # tests
    do = [
        (10, [5, 11, 21, 26]),
        (5, [5, 11, 16, 21, 26]),
        (100, [11, 26]),
    ]


class CalcBreaksUTF8Test(CalcBreaksTest, unittest.TestCase):
    def setUp(self):
        urwid.set_encoding("utf-8")

    mode = 'space'
    text = '\xe6\x9b\xbf\xe6\xb4\xbc\xe6\xb8\x8e\xe6\xba\x8f\xe6\xbd\xba'
    do = [
        (4, [6, 12, 15]),
        (10, [15]),
        (5, [6, 12, 15]),
    ]


class CalcBreaksCantDisplayTest(unittest.TestCase):
    def test(self):
        urwid.set_encoding("euc-jp")
        self.assertRaises(text_layout.CanNotDisplayText,
                          layout.calculate_text_segments,
                          B('\xA1\xA1'), 1, 'space')
        urwid.set_encoding("utf-8")
        self.assertRaises(text_layout.CanNotDisplayText,
                          layout.calculate_text_segments,
                          B('\xe9\xa2\x96'), 1, 'space')
        self.assertEqual(layout.layout(B('\xe9\xa2\x96'), 1, 'left', 'space'),
                         [[]])


class SubsegTest(unittest.TestCase):
    def setUp(self):
        urwid.set_encoding("euc-jp")

    def st(self, seg, text, start, end, exp):
        text = B(text)
        s = urwid.LayoutSegment(seg)
        result = s.subseg(text, start, end)
        assert result == exp, "Expected %r, got %r" % (exp, result)

    def test1_padding(self):
        self.st((10, None), "", 0, 8,    [(8, None)])
        self.st((10, None), "", 2, 10, [(8, None)])
        self.st((10, 0), "", 3, 7,     [(4, 0)])
        self.st((10, 0), "", 0, 20,     [(10, 0)])

    def test2_text(self):
        self.st((10, 0, B("1234567890")), "", 0, 8,  [(8, 0, B("12345678"))])
        self.st((10, 0, B("1234567890")), "", 2, 10, [(8, 0, B("34567890"))])
        self.st((10, 0, B("12\xA1\xA156\xA1\xA190")), "", 2, 8,
                [(6, 0, B("\xA1\xA156\xA1\xA1"))])
        self.st((10, 0, B("12\xA1\xA156\xA1\xA190")), "", 3, 8,
                [(5, 0, B(" 56\xA1\xA1"))])
        self.st((10, 0, B("12\xA1\xA156\xA1\xA190")), "", 2, 7,
                [(5, 0, B("\xA1\xA156 "))])
        self.st((10, 0, B("12\xA1\xA156\xA1\xA190")), "", 3, 7,
                [(4, 0, B(" 56 "))])
        self.st((10, 0, B("12\xA1\xA156\xA1\xA190")), "", 0, 20,
                [(10, 0, B("12\xA1\xA156\xA1\xA190"))])

    def test3_range(self):
        t = "1234567890"
        self.st((10, 0, 10), t, 0, 8,    [(8, 0, 8)])
        self.st((10, 0, 10), t, 2, 10, [(8, 2, 10)])
        self.st((6, 2, 8), t, 1, 6,     [(5, 3, 8)])
        self.st((6, 2, 8), t, 0, 5,     [(5, 2, 7)])
        self.st((6, 2, 8), t, 1, 5,     [(4, 3, 7)])
        t = "12\xA1\xA156\xA1\xA190"
        self.st((10, 0, 10), t, 0, 8,    [(8, 0, 8)])
        self.st((10, 0, 10), t, 2, 10, [(8, 2, 10)])
        self.st((6, 2, 8), t, 1, 6,     [(1, 3), (4, 4, 8)])
        self.st((6, 2, 8), t, 0, 5,     [(4, 2, 6), (1, 6)])
        self.st((6, 2, 8), t, 1, 5,     [(1, 3), (2, 4, 6), (1, 6)])


class CalcTranslateTest(object):
    def setUp(self):
        urwid.set_encoding("utf-8")

    def test1_left(self):
        result = urwid.default_layout.layout(self.text, self.width, 'left',
                                             self.mode)
        assert result == self.result_left, result

    def test2_right(self):
        result = urwid.default_layout.layout(self.text, self.width, 'right',
                                             self.mode)
        assert result == self.result_right, result

    def test3_center(self):
        result = urwid.default_layout.layout(self.text, self.width, 'center',
                                             self.mode)
        assert result == self.result_center, result


class CalcTranslateCharTest(CalcTranslateTest, unittest.TestCase):
    text = "It's out of control!\nYou've got to"
    mode = 'any'
    width = 15
    result_left = [
        [(15, 0, 15)],
        [(5, 15, 20), (0, 20)],
        [(13, 21, 34), (0, 34)]]
    result_right = [
        [(15, 0, 15)],
        [(10, None), (5, 15, 20), (0, 20)],
        [(2, None), (13, 21, 34), (0, 34)]]
    result_center = [
        [(15, 0, 15)],
        [(5, None), (5, 15, 20), (0, 20)],
        [(1, None), (13, 21, 34), (0, 34)]]


class CalcTranslateWordTest(CalcTranslateTest, unittest.TestCase):
    text = "It's out of control!\nYou've got to"
    mode = 'space'
    width = 14
    result_left = [
        [(11, 0, 11), (0, 11)],
        [(8, 12, 20), (0, 20)],
        [(13, 21, 34), (0, 34)]]
    result_right = [
        [(3, None), (11, 0, 11), (0, 11)],
        [(6, None), (8, 12, 20), (0, 20)],
        [(1, None), (13, 21, 34), (0, 34)]]
    result_center = [
        [(2, None), (11, 0, 11), (0, 11)],
        [(3, None), (8, 12, 20), (0, 20)],
        [(1, None), (13, 21, 34), (0, 34)]]


class CalcTranslateWordTest2(CalcTranslateTest, unittest.TestCase):
    text = "It's out of control!\nYou've got to "
    mode = 'space'
    width = 14
    result_left = [
        [(11, 0, 11), (0, 11)],
        [(8, 12, 20), (0, 20)],
        [(14, 21, 35), (0, 35)]]
    result_right = [
        [(3, None), (11, 0, 11), (0, 11)],
        [(6, None), (8, 12, 20), (0, 20)],
        [(14, 21, 35), (0, 35)]]
    result_center = [
        [(2, None), (11, 0, 11), (0, 11)],
        [(3, None), (8, 12, 20), (0, 20)],
        [(14, 21, 35), (0, 35)]]


class CalcTranslateWordTest3(CalcTranslateTest, unittest.TestCase):
    def setUp(self):
        urwid.set_encoding('utf-8')

    text = B('\xe6\x9b\xbf\xe6\xb4\xbc\n\xe6\xb8\x8e\xe6\xba\x8f\xe6\xbd\xba')
    width = 10
    mode = 'space'
    result_left = [
        [(4, 0, 6), (0, 6)],
        [(6, 7, 16), (0, 16)]]
    result_right = [
        [(6, None), (4, 0, 6), (0, 6)],
        [(4, None), (6, 7, 16), (0, 16)]]
    result_center = [
        [(3, None), (4, 0, 6), (0, 6)],
        [(2, None), (6, 7, 16), (0, 16)]]


class CalcTranslateWordTest4(CalcTranslateTest, unittest.TestCase):
    text = ' Die Gedank'
    width = 3
    mode = 'space'
    result_left = [
        [(0, 0)],
        [(3, 1, 4), (0, 4)],
        [(3, 5, 8)],
        [(3, 8, 11), (0, 11)]]
    result_right = [
        [(3, None), (0, 0)],
        [(3, 1, 4), (0, 4)],
        [(3, 5, 8)],
        [(3, 8, 11), (0, 11)]]
    result_center = [
        [(2, None), (0, 0)],
        [(3, 1, 4), (0, 4)],
        [(3, 5, 8)],
        [(3, 8, 11), (0, 11)]]


class CalcTranslateWordTest5(CalcTranslateTest, unittest.TestCase):
    text = ' Word.'
    width = 3
    mode = 'space'
    result_left = [[(3, 0, 3)], [(3, 3, 6), (0, 6)]]
    result_right = [[(3, 0, 3)], [(3, 3, 6), (0, 6)]]
    result_center = [[(3, 0, 3)], [(3, 3, 6), (0, 6)]]


class CalcTranslateClipTest(CalcTranslateTest, unittest.TestCase):
    text = "It's out of control!\nYou've got to\n\nturn it off!!!"
    mode = 'clip'
    width = 14
    result_left = [
        [(20, 0, 20), (0, 20)],
        [(13, 21, 34), (0, 34)],
        [(0, 35)],
        [(14, 36, 50), (0, 50)]]
    result_right = [
        [(-6, None), (20, 0, 20), (0, 20)],
        [(1, None), (13, 21, 34), (0, 34)],
        [(14, None), (0, 35)],
        [(14, 36, 50), (0, 50)]]
    result_center = [
        [(-3, None), (20, 0, 20), (0, 20)],
        [(1, None), (13, 21, 34), (0, 34)],
        [(7, None), (0, 35)],
        [(14, 36, 50), (0, 50)]]


class CalcTranslateCantDisplayTest(CalcTranslateTest, unittest.TestCase):
    text = B('Hello\xe9\xa2\x96')
    mode = 'space'
    width = 1
    result_left = [[]]
    result_right = [[]]
    result_center = [[]]


class CalcPosTest(unittest.TestCase):
    def setUp(self):
        self.text = "A" * 27
        self.trans = [
            [(2, None), (7, 0, 7), (0, 7)],
            [(13, 8, 21), (0, 21)],
            [(3, None), (5, 22, 27), (0, 27)]]
        self.mytests = [(1, 0, 0), (2, 0, 0), (11, 0, 7),
                        (-3, 1, 8), (-2, 1, 8), (1, 1, 9), (31, 1, 21),
                        (1, 2, 22), (11, 2, 27)]

    def tests(self):
        for x, y, expected in self.mytests:
            got = text_layout.calc_pos(self.text, self.trans, x, y)
            assert got == expected, "%r got:%r expected:%r" % ((x, y), got,
                                                               expected)


class Pos2CoordsTest(unittest.TestCase):
    pos_list = [5, 9, 20, 26]
    text = "1234567890" * 3
    mytests = [
        ([[(15, 0, 15)], [(15, 15, 30), (0, 30)]],
            [(5, 0), (9, 0), (5, 1), (11, 1)]),
        ([[(9, 0, 9)], [(12, 9, 21)], [(9, 21, 30), (0, 30)]],
            [(5, 0), (0, 1), (11, 1), (5, 2)]),
        ([[(2, None), (15, 0, 15)], [(2, None), (15, 15, 30), (0, 30)]],
            [(7, 0), (11, 0), (7, 1), (13, 1)]),
        ([[(3, 6, 9), (0, 9)], [(5, 20, 25), (0, 25)]],
            [(0, 0), (3, 0), (0, 1), (5, 1)]),
        ([[(10, 0, 10), (0, 10)]],
            [(5, 0), (9, 0), (10, 0), (10, 0)]),

        ]

    def test(self):
        for t, answer in self.mytests:
            for pos, a in zip(self.pos_list, answer):
                r = text_layout.calc_coords(self.text, t, pos)
                assert r == a, "%r got: %r expected: %r" % (t, r, a)


#################################################
# Tests for clipping without tabs
#################################################

class CalcClipCharTest(CalcBreaksTest, unittest.TestCase):
    mode = 'clip'
    text = "abfghsdjf askhtrvs\naltjhgsdf ljahtshgf"
    # tests
    do = [
        (100, [18, 38]),
        (6, [18, 38]),
        (10, [18, 38]),
    ]


class CalcClipDBCharTest(CalcBreaksTest, unittest.TestCase):
    def setUp(self):
        urwid.set_encoding("euc-jp")

    mode = 'clip'
    text = "abfgh\xA1\xA1j\xA1\xA1xskhtrvs\naltjhgsdf\xA1\xA1jahtshgf"
    # tests
    do = [
        (10, [18, 38]),
        (6, [18, 38]),
        (100, [18, 38]),
    ]


class CalcClipUTF8Test(CalcBreaksTest, unittest.TestCase):
    def setUp(self):
        urwid.set_encoding("utf-8")

    mode = 'clip'
    text = '\xe6\x9b\xbf\xe6\xb4\xbc\xe6\xb8\x8e\xe6\xba\x8f\xe6\xbd\xba'
    do = [
        (4, [15]),
        (10, [15]),
        (5, [15]),
    ]


#################################################
# Tests for layouts with tabs
#################################################

class CalcClipCharTabTest(CalcTabTest, unittest.TestCase):
    mode = 'clip'
    text = "abfg\tsdjf\taskhtrvs\naltjhgsdf ljahtshgf"
    # tests
    do = [
        (100, [[4, 4, 9, 9, 18, 18], [38, 38]]),
        (6, [[4, 4, 9, 9, 18, 18], [38, 38]]),
        (10, [[4, 4, 9, 9, 18, 18], [38, 38]]),
    ]


class CalcClipDBCharTabTest(CalcTabTest, unittest.TestCase):
    def setUp(self):
        urwid.set_encoding("euc-jp")

    mode = 'clip'
    text = "abfgh\xA1\t\xA1j\xA1\xA1xskhtrv\naltjh\tsdf\xA1\xA1jahtshgf"
    # tests
    do = [
        (10, [[6, 6, 18, 18], [24, 24, 38, 38]]),
        (6, [[6, 6, 18, 18], [24, 24, 38, 38]]),
        (100, [[6, 6, 18, 18], [24, 24, 38, 38]]),
    ]


class CalcClipUTF8TabTest(CalcTabTest, unittest.TestCase):
    def setUp(self):
        urwid.set_encoding("utf-8")

    mode = 'clip'
    text = '\xe6\x9b\xbf\xe6\xb4\xbc\t\xe6\xb8\x8e\xe6\xba\x8f\t\xe6\xbd\xba'
    do = [
        (4, [[6, 6, 13, 13, 17, 17]]),
        (10, [[6, 6, 13, 13, 17, 17]]),
        (5, [[6, 6, 13, 13, 17, 17]]),
    ]


class CalcClipCharMultiTabTest(CalcTabTest, unittest.TestCase):
    mode = 'clip'
    text = "\t\tabfg ssdjf\tatrvs\naltj\t\tsdf ljahtshgf"
    # tests
    do = [
        (100, [[0, 1, 12, 12, 18, 18], [23, 23, 24, 38, 38]]),
        (10, [[0, 1, 12, 12, 18, 18], [23, 23, 24, 38, 38]]),
        (6, [[0, 1, 12, 12, 18, 18], [23, 23, 24, 38, 38]]),
    ]


class CalcBreaksCharTabTest(CalcTabTest, unittest.TestCase):
    mode = 'any'
    text = "abfg\tsdjf\taskhtrvs\naltjhgsdf ljahtshgf"
    # tests
    do = [
        (100, [[4, 4, 9, 9, 18, 18], [38, 38]]),
        (6, [[4, 4], [9, 9], [16, 16], [18, 18], [25, 25],
             [31, 31], [37, 37], [38, 38]]),
        (10, [[4, 4, 7, 7], [9, 9, 12, 12], [18, 18],
              [29, 29], [38, 38]]),
    ]


class CalcBreaksCharTabTest2(CalcTabTest, unittest.TestCase):
    mode = 'any'
    text = "abfg\tsd f askh rvs\nalt\thgsdf ljahtshgf"
    # tests
    do = [
        (100, [[4, 4, 18, 18], [3, 3, 38, 38]]),
        (6, [[4, 4], [11, 11], [17, 17], [18, 18], [22, 22],
             [29, 29], [35, 35], [38, 38]]),
        (20, [[4, 4, 17, 17], [18, 18], [22, 22, 35, 35], [38, 38]]),
    ]


class CalcBreaksDBCharTabTest(CalcTabTest, unittest.TestCase):
    def setUp(self):
        urwid.set_encoding("euc-jp")

    mode = 'any'
    text = "abf\th\xA1\xA1j\xA1\xA1z\tkhtrvs\naltj\tgsdf\xA1\xA1jahts\tgf"
    # tests

    do = [
        (10, [[3, 3, 5, 5], [11, 11, 14, 14], [18, 18], [23, 23, 26, 26],
              [35, 35], [38, 38]]),
        (6, [[3, 3], [10, 10], [11, 11], [18, 18], [23, 23], [30, 30],
             [35, 35], [38, 38]]),
        (100, [[3, 3, 11, 11, 18, 18], [23, 23, 35, 35, 38, 38]]),
    ]


class CalcBreaksCharMultiTabTest(CalcTabTest, unittest.TestCase):
    mode = 'any'
    text = "\t\tabfg ssdjf\tatrvs\naltj\t\tsdf ljahtshgf"
    # tests
    do = [
        (100, [[0, 1, 12, 12, 18, 18], [23, 23, 24, 38, 38]]),
        (10, [[0, 1], [12, 12], [18, 18], [23, 23, 24], [35, 35], [38, 38]]),
        (6, [[0], [1], [8, 8], [12, 12], [18, 18], [23, 23], [24], [31, 31],
             [37, 37], [38, 38]]),
    ]


class CalcBreaksSpaceTabTest(CalcTabTest, unittest.TestCase):
    mode = 'space'
    text = "abfg\tsdjf\taskhtrvs\naltjhgsdf ljahtshgf"
    # tests
    do = [
        (100, [[4, 4, 9, 9, 18, 18], [38, 38]]),
        (6, [[4, 4], [9, 9], [16], [18, 18], [25], [31], [37], [38, 38]]),
        (10, [[4, 4], [9, 9], [18, 18], [28, 28], [38, 38]]),
    ]


class CalcBreaksSpaceTabTest2(CalcTabTest, unittest.TestCase):
    mode = 'space'
    text = "abfg\tsd f askh rvs\nalt\thgsdf ljahtshgf"
    # tests
    do = [
        (100, [[4, 4, 18, 18], [22, 22, 38, 38]]),
        (6, [[4, 4], [9, 9], [14, 14], [18, 18], [22, 22], [29], [35],
             [38, 38]]),
        (10, [[4, 4, 7, 7], [18, 18], [22, 22], [28, 28], [38, 38]]),
    ]


class CalcBreaksDBSpaceTabTest(CalcTabTest, unittest.TestCase):
    def setUp(self):
        urwid.set_encoding("euc-jp")

    mode = 'space'
    text = "abf\th\xA1\xA1j\xA1\xA1z\tkhtrvs\naltj\tgsdf\xA1\xA1jahts\tgf"
    # tests

    do = [
        (10, [[3, 3, 5], [11, 11], [18, 18], [23, 23], [30],
              [35, 35, 38, 38]]),
        (6, [[3, 3], [10], [11, 11], [18, 18], [23, 23], [30], [35, 35],
             [38, 38]]),
        (100, [[3, 3, 11, 11, 18, 18], [23, 23, 35, 35, 38, 38]]),
    ]


class CalcBreaksSpaceTabBugs(CalcTabTest, unittest.TestCase):
    # Some encountered bugs in tab layouts

    mode = 'space'
    text = '#    \tLicense \tas \tpublished \tby the Free Software ' \
           'Foundation; either\n'

    do = [
        (60, [[5, 5, 14, 14, 18, 18, 29, 29, 41, 41], [69, 69], [70]]),
        (42, [[5, 5, 14, 14, 18, 18, 29, 29], [69, 69], [70]])
    ]


class CalcBreaksSpaceMultiTabTest(CalcTabTest, unittest.TestCase):
    mode = 'space'
    text = "\t\tabfg ssdjf\tatrvs\naltj\t\tsdf ljahtshgf"
    # tests
    do = [
        (100, [[0, 1, 12, 12, 18, 18], [23, 23, 24, 38, 38]]),
        (10, [[0, 1], [12, 12], [18, 18], [23, 23, 24], [28, 28], [38, 38]]),
        (6, [[0], [1], [6, 6], [12, 12], [18, 18], [23, 23], [24], [31], [37],
             [38, 38]]),
    ]


#################################################
# DOS and other line-endings
#################################################


class DOSNewlineTest(CalcBreaksTest, unittest.TestCase):
    mode = 'any'
    text = "abfghsdjf askhtrvs\r\naltjhgsdf ljahtshgf"
    # tests
    do = [
        (100, [18, 39]),
        (6, [6, 12, 18, 26, 32, 38, 39]),
        (10, [10, 18, 30, 39]),
    ]


class MacNewlineTest(CalcBreaksTest, unittest.TestCase):
    mode = 'any'
    text = "abfghsdjf askhtrvs\raltjhgsdf ljahtshgf"
    # tests
    do = [
        (100, [18, 38]),
        (6, [6, 12, 18, 25, 31, 37, 38]),
        (10, [10, 18, 29, 38]),
    ]


class BBCNewlineTest(CalcBreaksTest, unittest.TestCase):
    mode = 'clip'
    text = "abfghsdjf askhtrvs\n\raltjhgsdf ljahtshgf"
    # tests
    do = [
        (100, [18, 39]),
        (6, [18, 39]),
        (10, [18, 39]),
    ]

# No, we don't support QNX, Atari or non-ASCII derived charsets.


class EmptyLinesClipTest(CalcBreaksTest, unittest.TestCase):
    mode = 'clip'
    text = "abfghsdjf askhtrv\n\nsltjhgsdf ljahtshgf\n"
    # tests
    do = [
        (100, [17, 18, 38, 39]),
        (6, [17, 18, 38, 39]),
        (10, [17, 18, 38, 39]),
    ]


class EmptyLinesAnyTest(CalcBreaksTest, unittest.TestCase):
    mode = 'any'
    text = "abfghsdjf askhtrv\n\nsltjhgsdf ljahtshgf\n"
    # tests
    do = [
        (100, [17, 18, 38, 39]),
        (6, [6, 12, 17, 18, 25, 31, 37, 38, 39]),
        (10, [10, 17, 18, 29, 38, 39]),
    ]


class EmptyLinesSpaceTest(CalcBreaksTest, unittest.TestCase):
    mode = 'space'
    text = "abfghsdjf askhtrv\n\nsltjhgsdf ljahtshgf\n"
    # tests
    do = [
        (100, [17, 18, 38, 39]),
        (6, [6, 12, 17, 18, 25, 31, 37, 38, 39]),
        (10, [9, 17, 18, 28, 38, 39]),
    ]
