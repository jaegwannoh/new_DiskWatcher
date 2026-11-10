# -*- coding: utf-8 -*-
"""리눅스(SSH), 윈도우(공유 폴더) 디스크 용량 확인"""
import ctypes
import datetime
import paramiko


def size_text(size):
    """바이트 -> '512.0MB', '48.0GB', '1.74TB'"""
    if size >= 1024 ** 4:
        return '%.2fTB' % (size / 1024.0 ** 4)
    if size >= 1024 ** 3:
        return '%.1fGB' % (size / 1024.0 ** 3)
    return '%.1fMB' % (size / 1024.0 ** 2)


def win_usage(path):
    """윈도우 경로 -> (시각, 전체 바이트, 사용 바이트, 사용률%). 시각은 PC 시각
    실패하면 WindowsError"""
    total = ctypes.c_ulonglong()
    free = ctypes.c_ulonglong()
    ok = ctypes.windll.kernel32.GetDiskFreeSpaceExW(
        path, None, ctypes.byref(total), ctypes.byref(free))
    if not ok:
        raise ctypes.WinError()
    used = total.value - free.value
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return now, total.value, used, int(used * 100.0 / total.value + 0.5)


def linux_usage(t):
    """Target -> (시각, 전체 바이트, 사용 바이트, 사용률%). 시각은 서버 시각
    실패하면 예외"""
    client = None
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(t.ip, t.port, t.user, t.pw, timeout=10,
                       allow_agent=False, look_for_keys=False)
        cmd = "date '+%Y-%m-%d %H:%M:%S'; LC_ALL=C df -P -k '" + t.path + "'"
        stdin, stdout, stderr = client.exec_command(cmd.encode('utf-8'), timeout=60)
        lines = stdout.read().splitlines()
        # [0] 2026-11-09 14:05:12
        # [1] Filesystem  1024-blocks  Used  Available  Capacity  Mounted on
        # [2] /dev/sdb1   2147483648   ...                87%       /data
        if len(lines) < 3:
            raise IOError(stderr.read().strip() or 'df failed')
        f = lines[-1].split()
        return lines[0].strip(), int(f[1]) * 1024, int(f[2]) * 1024, int(f[4].rstrip('%'))
    finally:
        if client is not None:
            client.close()


if __name__ == '__main__':
    # 시험: python disk.py
    from config import Target

    now, total, used, pct = win_usage(u'C:\\')
    print 'C:\\ ->', now, size_text(used), '/', size_text(total), pct, '%'
    try:
        win_usage(u'Q:\\')
    except WindowsError as ex:
        print 'Q:\\ ->', ex

    for ip, port in [('127.0.0.1', 22), ('10.255.255.1', 22)]:
        t = Target('linux', 'TEST', '/', 90, ip, port, 'root', '1234')
        try:
            now, total, used, pct = linux_usage(t)
            print ip, '->', now, size_text(used), '/', size_text(total), pct, '%'
        except Exception as ex:
            print ip, '->', type(ex).__name__, ex
