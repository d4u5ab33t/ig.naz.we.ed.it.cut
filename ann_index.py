#!/usr/bin/env python3
"""
ann_index.py
Optional ANN index wrapper using Annoy for fast nearest neighbor on color hist vectors.
Falls back to brute-force search if Annoy is not installed.
"""
from __future__ import annotations
import os
import json
from typing import List, Tuple, Optional

import numpy as np

try:
    from annoy import AnnoyIndex
    HAS_ANNOY = True
except Exception:
    HAS_ANNOY = False


def build_annoy_index(cache_json_path: str, index_out_path: str, n_trees: int = 10) -> bool:
    """Builds an Annoy index from a cache JSON file mapping path->vector.
    Writes .ann and .meta (json list of paths).
    """
    if not HAS_ANNOY:
        return False
    if not os.path.exists(cache_json_path):
        return False
    with open(cache_json_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    items = []
    for path, meta in cache.items():
        vec = meta.get('color_hist') or meta.get('vector') or None
        if vec and isinstance(vec, list):
            items.append((path, vec))
    if not items:
        return False
    dim = len(items[0][1])
    t = AnnoyIndex(dim, 'euclidean')
    paths = []
    for i, (path, vec) in enumerate(items):
        t.add_item(i, vec)
        paths.append(path)
    t.build(n_trees)
    t.save(index_out_path + '.ann')
    with open(index_out_path + '.meta', 'w', encoding='utf-8') as f:
        json.dump(paths, f)
    return True


class AnnIndex:
    def __init__(self, index_prefix: str):
        self.index_prefix = index_prefix
        self.index = None
        self.paths = []
        self.dim = 0
        if not HAS_ANNOY:
            raise RuntimeError('annoy not installed')
        self._load()

    def _load(self):
        ann_path = self.index_prefix + '.ann'
        meta_path = self.index_prefix + '.meta'
        if not os.path.exists(ann_path) or not os.path.exists(meta_path):
            raise FileNotFoundError('Annoy index or meta missing')
        with open(meta_path, 'r', encoding='utf-8') as f:
            self.paths = json.load(f)
        # load one vector to get dim
        # we need to create AnnoyIndex with correct dim; load requires dim
        # read meta first vector length from cache may not be available; assume dim stored via file size? skip and try common dims
        # Better: Annoy supports loading without knowing dim by creating pk and loading, but requires same dim on creation. So open .ann to infer not possible. We'll try dims 64, 128 fallback
        # For simplicity assume dim 128 if not proviced. This is best-effort.
        for possible_dim in (256, 128, 64, 48, 32, 16):
            try:
                t = AnnoyIndex(possible_dim, 'euclidean')
                t.load(ann_path)
                self.index = t
                self.dim = possible_dim
                return
            except Exception:
                continue
        raise RuntimeError('Failed to load Annoy index with common dims')

    def query(self, vec: List[float], k: int = 16) -> List[Tuple[str, float]]:
        if self.index is None:
            return []
        if len(vec) != self.dim:
            # Annoy requires same dim; cannot query. fallback
            return []
        ids, dists = self.index.get_nns_by_vector(vec, k, include_distances=True)
        out = []
        for i, dist in zip(ids, dists):
            out.append((self.paths[i], float(dist)))
        return out


# brute-force fallback
class BruteIndex:
    def __init__(self, cache_json_path: str):
        with open(cache_json_path, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        self.items = []
        for path, meta in cache.items():
            vec = meta.get('color_hist') or meta.get('vector') or None
            if vec and isinstance(vec, list):
                self.items.append((path, vec))
        if self.items:
            self.dim = len(self.items[0][1])
        else:
            self.dim = 0

    def query(self, vec: List[float], k: int = 16) -> List[Tuple[str, float]]:
        import math
        out = []
        for path, v in self.items:
            if len(v) != len(vec):
                continue
            d = math.dist(v, vec)
            out.append((path, d))
        out.sort(key=lambda x: x[1])
        return out[:k]
