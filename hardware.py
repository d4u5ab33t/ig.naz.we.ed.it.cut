#!/usr/bin/env python3
"""hardware.py - detect platform and available acceleration/hw"""
import platform
import shutil
import subprocess


def detect_gpu():
    # check for nvidia-smi and ffmpeg encoders
    try:
        res = subprocess.run(['nvidia-smi','-L'], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and 'GPU' in res.stdout:
            return 'nvidia'
    except Exception:
        pass
    # check ffmpeg encoders
    try:
        r = subprocess.run(['ffmpeg','-hide_banner','-encoders'], capture_output=True, text=True, timeout=3)
        out = r.stdout
        if 'h264_nvenc' in out:
            return 'nvenc'
        if 'h264_qsv' in out:
            return 'qsv'
        if 'h264_amf' in out:
            return 'amf'
    except Exception:
        pass
    return None


def cpu_info():
    return platform.processor() or platform.machine()

if __name__ == '__main__':
    print('cpu:', cpu_info())
    print('gpu:', detect_gpu())
