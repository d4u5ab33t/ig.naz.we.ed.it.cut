#!/usr/bin/env python3
# hardware.py
"""
Hardware detection & optimization helpers. Lightweight and cross-platform.
"""
from __future__ import annotations

import platform
import shutil
import subprocess
from typing import Dict


def detect_hardware() -> Dict:
    info = {}
    info['platform'] = platform.system()
    info['machine'] = platform.machine()

    # CPU
    try:
        import psutil
        info['cpu_count_logical'] = psutil.cpu_count()
        info['memory_total_gb'] = round(psutil.virtual_memory().total / (1024**3), 1)
    except Exception:
        info['cpu_count_logical'] = None
        info['memory_total_gb'] = None

    # GPU (NVIDIA detection via nvidia-smi)
    nvidia = shutil.which('nvidia-smi')
    if nvidia:
        try:
            out = subprocess.run(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'], capture_output=True, text=True, timeout=3)
            lines = out.stdout.strip().splitlines()
            info['gpus'] = [l.strip() for l in lines if l.strip()]
        except Exception:
            info['gpus'] = []
    else:
        info['gpus'] = []

    # Raspberry Pi detection
    try:
        with open('/proc/device-tree/model','r') as f:
            model = f.read().lower()
            info['is_raspberry_pi'] = 'raspberry' in model
    except Exception:
        info['is_raspberry_pi'] = False

    return info


if __name__ == '__main__':
    import json
    print(json.dumps(detect_hardware(), indent=2))
