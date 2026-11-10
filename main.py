# -*- coding: utf-8 -*-
"""DiskWatcher 시작점.  실행: pythonw.exe main.py"""
import sys
reload(sys)
sys.setdefaultencoding('utf-8')    # 한글 str/unicode 섞여도 오류 안 나게

import sip
sip.setapi('QString', 2)           # QString 없이 파이썬 문자열 그대로 (PyQt4 import 전에)
sip.setapi('QVariant', 2)

import ctypes
from PyQt4.QtGui import QApplication
from ui_main import MainWindow

# 작업 표시줄에서 "파이썬"이 아니라 별도 프로그램으로 보이게 (창 아이콘이 그대로 나옴)
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u'DiskWatcher')
app = QApplication(sys.argv)
win = MainWindow()
win.show()
sys.exit(app.exec_())
