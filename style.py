# -*- coding: utf-8 -*-
"""스타일시트 (색, 글자 크기). px = 기본 글자 크기 (pt는 Windows 배율에 따라 커져서 px 사용)"""

QSS = '''
QWidget { font-family: "Malgun Gothic"; font-size: %(px)dpx; color: #1F2933; }
#main { background: #EEF1F4; }
#main[over="true"] { background: #B71C1C; }

#tools { background: white; border: 1px solid #D5DAE0; border-radius: 6px; margin-right: 14px; }
QPushButton { padding: 4px 12px; background: white;
              border: 1px solid #B8C1CB; border-radius: 4px;
              qproperty-iconSize: %(px)dpx %(px)dpx; }
QPushButton:hover { background: #F0F3F6; }

#alert { background: white; border: 1px solid #D5DAE0; border-radius: 6px; margin-right: 14px; }
#alert[warn="true"] { background: #FFE082; border-color: #F9A825; }
#msg { color: #B71C1C; font-weight: bold; margin-left: 12px; }

QScrollArea, #cards { background: transparent; border: none; }
QScrollBar:vertical { width: 14px; background: transparent; }
QScrollBar::handle:vertical { background: #9AA5B1; border-radius: 4px;
                              margin-left: 6px; min-height: 30px; }
QScrollBar::handle:vertical:disabled { background: transparent; }
QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page { height: 0; background: none; }
#card { background: white; border: 1px solid #D5DAE0;
        border-left: 5px solid #1D5FBF; border-radius: 6px; }
#card[state="wait"] { border-left-color: #9AA5B1; }
#card[state="over"] { background: #FDECEA; border-left-color: #C62828; }
#card[state="fail"] { background: #F5F6F7; border-left-color: #9AA5B1; }
#name { font-weight: bold; }
#small { font-size: %(small)dpx; color: #52606D; }
#pct { font-size: %(big)dpx; font-weight: bold; }
'''


def make_style(px):
    """글자 크기 px에 맞춘 스타일시트"""
    return QSS % {'px': px, 'small': px - 2, 'big': px * 14 / 10}
