# -*- coding: utf-8 -*-
"""용량 로그: logs 폴더에 disk_YYYY-MM-DD.csv"""
import os
import codecs
import datetime

from disk import size_text

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
FORMAT = '%-19s,%-6s,%-10s,%4s,%5s,%9s,%9s,%s'


def write_log(results):
    """한 바퀴 결과를 기록. results = [(Target, 결과), ...]
    결과는 (시각, 전체, 사용, %), 실패했으면 None"""
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    now = datetime.datetime.now()
    path = os.path.join(LOG_DIR, now.strftime('disk_%Y-%m-%d.csv'))
    is_new = not os.path.exists(path)
    stamp = now.strftime('%Y-%m-%d %H:%M:%S')
    with codecs.open(path, 'a', 'utf-8') as f:
        if is_new:
            head = FORMAT % ('time', 'status', 'name', 'use', 'limit', 'used', 'total', 'path')
            f.write(u'\ufeff' + head + '\r\n')
        for t, usage in results:
            limit = str(t.limit) + '%'
            if usage is None:
                line = FORMAT % (stamp, '[FAIL]', t.name, '', limit, '', '', t.path)
            else:
                srv_time, total, used, pct = usage
                status = '[OVER]' if pct >= t.limit else '[OK]'
                line = FORMAT % (stamp, status, t.name, str(pct) + '%', limit,
                                 size_text(used), size_text(total), t.path)
            f.write(line + '\r\n')


def cleanup_logs(keep=30):
    """최근 keep 개만 남기고 오래된 로그 파일 삭제"""
    if not os.path.isdir(LOG_DIR):
        return
    names = sorted(n for n in os.listdir(LOG_DIR) if n.startswith('disk_') and n.endswith('.csv'))
    for name in names[:-keep]:
        try:
            os.remove(os.path.join(LOG_DIR, name))
        except OSError:
            pass    # 엑셀 등에서 열려 있으면 다음에 다시 시도


if __name__ == '__main__':
    # 시험: python log.py  -> logs 폴더에 오늘 날짜 파일이 생김
    from config import Target
    GB = 1024 ** 3
    write_log([
        (Target('linux', 'WEB1', '/var/log', 90), ('2026-11-09 14:05:12', 100 * GB, 48 * GB, 48)),
        (Target('linux', 'DB1', '/data', 80), ('2026-11-09 14:05:13', 2048 * GB, 1782 * GB, 87)),
        (Target('win', 'FILE1', r'\\10.0.0.31\data', 85), ('2026-11-09 14:05:14', 500 * GB, 310 * GB, 62)),
        (Target('linux', 'BATCH1', '/batch', 80), None),
    ])
    print 'written to', LOG_DIR

    # 가짜 로그 5개를 더 만들고 최근 3개만 남는지 확인
    for d in [1, 2, 10, 40, 100]:
        day = datetime.date.today() - datetime.timedelta(days=d)
        open(os.path.join(LOG_DIR, day.strftime('disk_%Y-%m-%d.csv')), 'w').close()
    print 'before:', sorted(os.listdir(LOG_DIR))
    cleanup_logs(3)
    print 'after :', sorted(os.listdir(LOG_DIR))
