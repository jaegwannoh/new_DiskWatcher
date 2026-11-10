# -*- coding: utf-8 -*-
"""용량 확인 작업: QThread 1개가 path를 파일 순서대로 한 바퀴 확인"""
from PyQt4.QtCore import QThread, pyqtSignal

from disk import win_usage, linux_usage
from log import write_log, cleanup_logs


class Worker(QThread):
    """한 바퀴만 확인하고 끝남. 다음 회차는 화면에서 새 Worker를 만듦"""
    one_done = pyqtSignal(int, object)   # (순번, 결과)  결과 = (시각, 전체, 사용, %) 또는 None
    all_done = pyqtSignal()

    def __init__(self, targets):
        QThread.__init__(self)
        self.targets = targets
        self.stop = False    # 새로고침, 창 닫기 때 True

    def run(self):
        results = []
        for i, t in enumerate(self.targets):
            if self.stop:
                break
            try:
                if t.kind == 'linux':
                    usage = linux_usage(t)
                else:
                    usage = win_usage(t.path)
            except Exception:
                usage = None
            results.append((t, usage))
            if not self.stop:
                self.one_done.emit(i, usage)
        try:
            write_log(results)       # 중단됐어도 확인한 만큼 기록
            cleanup_logs()
        except IOError:
            pass                     # 로그 파일이 엑셀 등에서 열려 있으면 이번 회차 기록은 건너뜀
        if not self.stop:
            self.all_done.emit()


if __name__ == '__main__':
    # 시험: python worker.py  (servers.txt 의 path를 한 바퀴 확인)
    import sys
    from PyQt4.QtCore import QCoreApplication
    from config import load_config

    def show(i, usage):
        print i, repr(usage)

    app = QCoreApplication(sys.argv)
    time_server, wait_min, targets, bad = load_config('servers.txt')
    w = Worker(targets)
    w.one_done.connect(show)
    w.all_done.connect(app.quit)
    w.start()
    app.exec_()
