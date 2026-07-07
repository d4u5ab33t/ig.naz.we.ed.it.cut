#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal hardware probing & optimization helpers.
Detects CPU cores, RAM, and NVIDIA GPU when available.
Provides simple profile used by the renderer to pick defaults.
"""
from __future__ import annotations
import platform
import shutil
import subprocess
import multiprocessing
import os


def probe_hardware() -> dict:
    info = {}
    info['platform'] = platform.system()
    info['machine'] = platform.machine()
    try:
        info['cpu_count'] = multiprocessing.cpu_count()
    except Exception:
        info['cpu_count'] = 1
    # RAM (Linux/Windows fallback)
    try:
        if info['platform'] == 'Windows':
            import psutil
            info['total_ram_gb'] = round(psutil.virtual_memory().total / (1024**3), 1)
        else:
            with open('/proc/meminfo') as f:
                for line in f:
                    if line.startswith('MemTotal'):
                        parts = line.split()
                        info['total_ram_gb'] = round(int(parts[1]) / 1024 / 1024, 1)
                        break
    except Exception:
        info['total_ram_gb'] = None

    # NVIDIA GPU detection (nvidia-smi)
    nvidia = shutil.which('nvidia-smi')
    if nvidia:
        try:
            out = subprocess.check_output([nvidia, '--query-gpu=name,memory.total', '--format=csv,noheader'], text=True)
            gpus = []
            for row in out.strip().splitlines():
                name, mem = [c.strip() for c in row.split(',')]
                gpus.append({'name': name, 'memory': mem})
            info['gpus'] = gpus
        except Exception:
            info['gpus'] = None
    else:
        info['gpus'] = None

    # Raspberry Pi quick detection
    info['is_raspberry_pi'] = os.path.exists('/proc/device-tree/model') and 'raspberry' in platform.uname().machine.lower()

    return info


def recommended_profile() -> dict:
    hw = probe_hardware()
    profile = {'use_gpu': False, 'threads': max(1, hw.get('cpu_count', 1) - 1), 'preset': 'veryfast'}
    if hw.get('gpus'):
        profile['use_gpu'] = True
        profile['preset'] = 'fast'
    if hw.get('is_raspberry_pi'):
        profile['threads'] = max(1, int(hw.get('cpu_count', 1) // 2))
        profile['preset'] = 'superfast'
    return profile


if __name__ == '__main__':
    import json
    print(json.dumps(probe_hardware(), indent=2))
