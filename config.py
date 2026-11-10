# -*- coding: utf-8 -*-
"""servers.txt 읽기"""
import codecs


class Target(object):
    """설정 파일 한 줄 = 서버 하나의 path 하나"""

    def __init__(self, kind, name, path, limit, ip='', port=22, user='', pw=''):
        self.kind = kind      # 'linux' 또는 'win'
        self.name = name      # 화면에 표시할 이름
        self.path = path      # 리눅스: /data   윈도우: \\10.0.0.31\data
        self.limit = limit    # 임계치 (%)
        self.ip = ip          # 아래 4개는 리눅스만 사용
        self.port = port
        self.user = user
        self.pw = pw


def parse_line(line):
    """한 줄 -> Target. 칸 수가 틀리거나 숫자가 아니면 ValueError"""
    f = [x.strip() for x in line.split('|')]
    kind = f[0].lower()
    if kind == 'linux' and len(f) == 8:
        # linux|이름|path|임계치|IP|포트|user|pw
        return Target(kind, f[1], f[2], int(f[3]), f[4], int(f[5]), f[6], f[7])
    if kind == 'win' and len(f) == 4:
        # win|이름|경로|임계치
        return Target(kind, f[1], f[2], int(f[3]))
    raise ValueError()


def load_config(path):
    """servers.txt -> (시간 기준 서버, 대기 분, Target 목록, 잘못된 줄 번호 목록)"""
    time_server = ''
    wait_min = 5
    targets = []
    bad = []
    lines = codecs.open(path, 'r', 'utf-8-sig').read().splitlines()
    for no, line in enumerate(lines, 1):
        line = line.strip()
        if line == '' or line.startswith('#') or (len(line) < 6):
            continue
        try:
            if line.startswith('TIME_SERVER='):
                time_server = line.split('=', 1)[1].strip()
            elif line.startswith('WAIT_MIN='):
                wait_min = int(line.split('=', 1)[1])
            else:
                targets.append(parse_line(line))
        except ValueError:
            bad.append(no)
    return time_server, wait_min, targets, bad


if __name__ == '__main__':
    # 시험: python config.py  (한글은 repr 로 출력)
    time_server, wait_min, targets, bad = load_config('servers.txt')
    print 'TIME_SERVER =', repr(time_server)
    print 'WAIT_MIN    =', wait_min
    print 'bad lines   =', bad
    for t in targets:
        print t.kind, repr(t.name), repr(t.path), t.limit, t.ip, t.port, t.user, t.pw
