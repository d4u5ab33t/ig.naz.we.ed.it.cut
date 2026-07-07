#!/usr/bin/env python3
"""
copy_favs.py
Copy newest FAVs*.html from configured path into ./data/FAVS.html
"""
from clip_pools import copy_latest_favs

if __name__ == '__main__':
    res = copy_latest_favs()
    if res:
        print('FAVs copied to', res)
    else:
        print('No FAVs found')
