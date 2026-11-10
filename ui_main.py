# -*- coding: utf-8 -*-
"""메인 화면"""
from __future__ import unicode_literals
import os
import codecs
from PyQt4.QtCore import Qt, QSize, QTimer
from PyQt4.QtGui import (QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout,
                         QSizePolicy, QPainter, QColor,
                         QMainWindow, QPushButton, QScrollArea, QStyle)

from config import load_config
from disk import size_text
from log import LOG_DIR
from worker import Worker
from style import make_style

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'servers.txt')


def set_prop(w, name, value):
    """스타일시트용 속성을 바꾸고 다시 적용 (예: #card[state="over"])"""
    w.setProperty(name, value)
    w.style().unpolish(w)
    w.style().polish(w)


class Bar(QWidget):
    """사용량 막대 (둥근 모양). 임계치 위치에 세로 선"""

    def __init__(self, limit):
        QWidget.__init__(self)
        self.limit = limit    # 임계치 (%)
        self.pct = 0          # 확인 중, 실패일 때는 0 (빈 막대)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def sizeHint(self):
        return QSize(100, self.fontMetrics().height())    # 높이 = 글자 한 줄

    def set_pct(self, pct):
        self.pct = pct
        self.update()         # 다시 그리기

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        r = h / 4.0                                          # 끝을 둥글게 (두께의 절반)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)               # 둥근 부분을 매끄럽게
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#E4E7EB'))
        p.drawRoundedRect(0, h / 4, w, h / 2, r, r)          # 바탕 (회색)
        if self.pct > 0:
            p.setBrush(QColor('#C62828' if self.pct >= self.limit else '#1D5FBF'))
            p.drawRoundedRect(0, h / 4, w * self.pct / 100, h / 2, r, r)
        p.fillRect(w * self.limit / 100 - 1, 0, 2, h, QColor('#52606D'))   # 임계치 선


class DiskCard(QFrame):
    """servers.txt 한 줄 = 카드 하나
    1줄: 이름  path ............ 사용/전체  %
    2줄: 막대 (카드 너비 전체)"""

    def __init__(self, t):
        QFrame.__init__(self)
        self.setObjectName('card')
        self.setToolTip(t.ip + '  ' + t.path if t.kind == 'linux' else t.path)
        self.t = t
        name_label = QLabel(t.name)
        name_label.setObjectName('name')
        path_label = QLabel(t.path)
        path_label.setObjectName('small')
        self.size_label = QLabel('확인 중...')
        self.size_label.setObjectName('small')
        self.pct_label = QLabel()
        self.pct_label.setObjectName('pct')
        self.bar = Bar(t.limit)
        top = QHBoxLayout()
        top.setSpacing(10)                    # 이름, path, 크기, % 사이 간격
        top.addWidget(name_label)
        top.addWidget(path_label)
        top.addStretch(1)
        top.addWidget(self.size_label)
        top.addWidget(self.pct_label)
        box = QVBoxLayout(self)
        box.setContentsMargins(14, 8, 14, 6)  # 카드 안쪽 여백 (왼, 위, 오른, 아래)
        box.setSpacing(0)                     # 글자 줄과 막대 사이 간격
        box.addLayout(top)
        box.addWidget(self.bar)
        self.set_state('wait')

    def set_state(self, state):
        """wait(확인 중), ok, over(초과), fail(실패). 색은 스타일시트에서 state 값으로 정함"""
        self.state = state
        set_prop(self, 'state', state)

    def set_usage(self, usage):
        """결과 표시. usage = (시각, 전체, 사용, %), 실패하면 None"""
        if usage is None:
            self.bar.set_pct(0)
            self.pct_label.setText('')
            self.size_label.setText('접속 실패')
            self.set_state('fail')
            return
        srv_time, total, used, pct = usage
        state = 'over' if pct >= self.t.limit else 'ok'
        self.bar.set_pct(pct)
        text = '%d%%' % pct
        if state == 'over':
            text = '<font color="#C62828">' + text + '</font>'
        self.pct_label.setText(text)
        self.size_label.setText(size_text(used) + ' / ' + size_text(total))
        self.set_state(state)


class MainWindow(QMainWindow):
    """메인 창: 도구 막대 / 알림 줄 / 카드 목록"""

    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle('DiskWatcher')
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DriveHDIcon))   # 하드디스크 그림
        self.worker = None       # 지금 확인 중인 Worker
        self.old_workers = []     # 중단했지만 아직 안 끝난 Worker (끝날 때까지 붙잡아 둠)
        self.cards = []           # DiskCard 목록 (servers.txt 순서)
        self.remain = 0           # 다음 확인까지 남은 초
        self.font_px = 0          # 지금 글자 크기 (px)
        if not os.path.isdir(LOG_DIR):
            os.makedirs(LOG_DIR)  # 첫 바퀴 전에 "로그 폴더"를 눌러도 열리게

        st = self.style()              # Qt 기본 그림 (아이콘)
        refresh_btn = QPushButton(st.standardIcon(QStyle.SP_BrowserReload), '새로고침 (F5)')
        refresh_btn.setShortcut('F5')
        refresh_btn.clicked.connect(self.reload)
        log_btn = QPushButton(st.standardIcon(QStyle.SP_DirOpenIcon), '로그 폴더')
        log_btn.clicked.connect(lambda: os.startfile(LOG_DIR))
        conf_btn = QPushButton(st.standardIcon(QStyle.SP_FileDialogDetailedView), '설정 열기')
        conf_btn.clicked.connect(self.open_config)
        self.time_label = QLabel()     # 마지막 갱신
        self.next_label = QLabel()     # 다음 확인까지
        tools = QFrame()               # 도구 막대 (흰색, 창 배경이 빨개져도 그대로)
        tools.setObjectName('tools')
        tools_box = QHBoxLayout(tools)
        tools_box.addWidget(self.time_label)
        tools_box.addSpacing(24)
        tools_box.addWidget(self.next_label)
        tools_box.addStretch(1)
        tools_box.addWidget(refresh_btn)
        tools_box.addWidget(log_btn)
        tools_box.addWidget(conf_btn)

        self.alert = QFrame()          # 알림 줄 (servers.txt 문제면 노랑)
        self.alert.setObjectName('alert')
        self.count_label = QLabel()    # 전체 5 · 정상 3 · 초과 1 · 실패 1
        self.msg_label = QLabel()      # ▲ 알림 내용
        self.msg_label.setObjectName('msg')
        self.msg_label.setWordWrap(True)  # 길면 여러 줄로 (창을 좁혀도 잘리지 않게)
        alert_box = QHBoxLayout(self.alert)
        alert_box.addWidget(self.count_label)
        alert_box.addWidget(self.msg_label, 1)

        self.scroll = QScrollArea()    # 카드 목록
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)     # 항상 자리를 차지 → 오른쪽 끝 맞춤
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sb = self.scroll.verticalScrollBar()          # 스크롤할 게 없으면 막대 손잡이 숨김
        sb.setEnabled(False)
        sb.rangeChanged.connect(lambda lo, hi: sb.setEnabled(hi > 0))
        self.main = QWidget()          # 창 배경 (초과면 빨강)
        self.main.setObjectName('main')
        box = QVBoxLayout(self.main)
        box.addWidget(tools)
        box.addWidget(self.alert)
        box.addWidget(self.scroll)
        self.setCentralWidget(self.main)

        self.timer = QTimer(self)      # 1초마다 카운트다운
        self.timer.timeout.connect(self.on_tick)
        self.resize(900, 700)
        self.reload()

    def open_config(self):
        """설정 열기. servers.txt가 없으면 적는 법만 들어 있는 파일을 만들고 엶"""
        if not os.path.exists(CONFIG):
            f = codecs.open(CONFIG, 'w', 'utf-8-sig')
            f.write('TIME_SERVER=\r\nWAIT_MIN=5\r\n\r\n'
                    '# linux|이름|path|임계치|IP|포트|user|pw\r\n'
                    '# win|이름|path|임계치\r\n')
            f.close()
        os.startfile(CONFIG)

    def reload(self):
        """servers.txt를 읽어 카드를 새로 만들고 확인 시작 (처음 켤 때, F5)"""
        try:
            self.time_server, self.wait_min, targets, self.bad = load_config(CONFIG)
        except (IOError, UnicodeDecodeError):     # 파일이 없음, 열 수 없음, UTF-8이 아님
            self.time_server, self.wait_min, targets, self.bad = '', 5, [], []
        self.cards = [DiskCard(t) for t in targets]
        inner = QWidget()
        inner.setObjectName('cards')
        box = QVBoxLayout(inner)
        box.setContentsMargins(0, 0, 0, 0)    # 카드 왼쪽 끝을 도구 막대, 알림 줄과 맞춤
        for card in self.cards:
            box.addWidget(card)
        self.scroll.setWidget(inner)      # 이전 카드 목록은 Qt가 지움
        self.update_alert()
        self.start_check()

    def start_check(self):
        """이전 Worker는 중단 표시만 하고, 새 Worker로 한 바퀴 확인"""
        self.timer.stop()
        if self.worker is not None:
            self.worker.stop = True               # 확인 중인 path 하나만 마저 하고 끝남
            self.old_workers.append(self.worker)
        self.old_workers = [w for w in self.old_workers if w.isRunning()]   # 끝난 것은 놓아줌
        if not self.cards:                        # servers.txt 문제 → 확인하지 않음
            self.worker = None
            self.next_label.setText('')
            return
        self.worker = Worker([c.t for c in self.cards])
        self.worker.one_done.connect(self.on_one_done)
        self.worker.all_done.connect(self.on_all_done)
        self.worker.start()
        self.next_label.setText('확인 중...')

    def on_one_done(self, i, usage):
        """path 하나 확인 끝 (Worker 시그널) → 카드 i 갱신"""
        if self.sender() is not self.worker:      # 새로고침 전에 보낸 늦은 결과는 버림
            return
        card = self.cards[i]
        card.set_usage(usage)
        if usage is not None and card.t.name == self.time_server:
            self.time_label.setText('마지막 갱신 ' + usage[0])
        self.update_alert()

    def on_all_done(self):
        """한 바퀴 끝 (Worker 시그널) → WAIT_MIN분 카운트다운 시작"""
        if self.sender() is not self.worker:
            return
        self.remain = self.wait_min * 60
        self.next_label.setText('다음 확인 %02d:00' % self.wait_min)
        self.timer.start(1000)

    def on_tick(self):
        """1초마다: 남은 시간 표시, 0이 되면 다시 확인"""
        self.remain -= 1
        if self.remain <= 0:
            self.start_check()
            return
        self.next_label.setText('다음 확인 %02d:%02d' % (self.remain / 60, self.remain % 60))

    def update_alert(self):
        """알림 줄, 창 배경(초과면 빨강)"""
        states = [c.state for c in self.cards]
        fail = '실패 %d' % states.count('fail')
        if 'fail' in states:
            fail = '<font color="#E65100">' + fail + '</font>'
        self.count_label.setText('전체 %d · 정상 %d · 초과 %d · %s' % (
            len(states), states.count('ok'), states.count('over'), fail))

        overs = ['%s %s %d%% (기준 %d%%)' % (c.t.name, c.t.path, c.bar.pct, c.t.limit)
                 for c in self.cards if c.state == 'over']
        msgs = []
        if self.bad:
            msgs.append('▲ servers.txt 오류 (%s번째 줄)' % ', '.join(str(n) for n in self.bad))
        elif not self.cards:
            msgs.append('▲ servers.txt를 설정해 주세요')
        if overs:                         # servers.txt 오류가 있어도 초과는 함께 보여 줌
            msgs.append('▲ 임계치 초과: ' + ', '.join(overs))
        self.msg_label.setText('    '.join(msgs))
        set_prop(self.alert, 'warn', bool(self.bad) or not self.cards)
        set_prop(self.main, 'over', bool(overs))

    def resizeEvent(self, event):
        """창 크기에 맞춰 글자 크기 조절 (스타일시트 font-size, 12~28px)"""
        px = max(12, min(28, self.width() / 64, self.height() / 50))
        if px != self.font_px:
            self.font_px = px
            self.setStyleSheet(make_style(px))
        QMainWindow.resizeEvent(self, event)

    def closeEvent(self, event):
        """창 닫기: 남은 Worker가 끝날 때까지 기다림 (path 하나 마저 끝나고 로그 기록)"""
        self.hide()
        self.timer.stop()
        for w in self.old_workers + [self.worker]:
            if w is not None:
                w.stop = True
                w.wait()          # 끝날 때까지 (창은 이미 숨김, 보통 10초 이내, 최악 70초쯤)
        event.accept()
