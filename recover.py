#!/usr/bin/env python3
"""
recover.py

Scan a KakaoTalk 'contents' folder (or app temporary files), detect MIME types using magic bytes,
add file extensions, and copy files into a date-organized output directory.

Usage:
  python3 recover.py -s /path/to/contents -o ./result

Requirement: python-magic (or python-magic-bin on Windows)
"""

import os
import time
import shutil
import argparse
import mimetypes
from pathlib import Path

try:
    import magic
except Exception:
    print("python-magic module not found. Install with: pip install python-magic (or on Windows: python-magic-bin)")
    raise

from tqdm import tqdm

# Simple MIME -> extension fallback mapping
FALLBACK_MAP = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/gif': 'gif',
    'video/mp4': 'mp4',
    'video/quicktime': 'mov',
    'audio/mpeg': 'mp3',
    'application/pdf': 'pdf',
}


def guess_ext(mime: str) -> str:
    if not mime:
        return 'bin'
    try:
        ext = mimetypes.guess_extension(mime)
    except Exception:
        ext = None
    if ext:
        return ext.lstrip('.')
    if mime in FALLBACK_MAP:
        return FALLBACK_MAP[mime]
    if '/' in mime:
        return mime.split('/')[-1]
    return 'bin'


def process(src_dir: str, out_dir: str, follow_symlinks: bool = False):
    src = Path(src_dir)
    out = Path(out_dir)
    if not src.exists():
        raise FileNotFoundError(f"Source folder not found: {src}")
    out.mkdir(parents=True, exist_ok=True)

    # Create magic object
    mg = magic.Magic(mime=True)

    # Count files
    total = 0
    for _ in src.rglob('*'):
        total += 1

    for path in tqdm(list(src.rglob('*')), desc='Scanning', total=total):
        if path.is_dir():
            continue
        try:
            mime = mg.from_file(str(path))
        except Exception:
            mime = None
        ext = guess_ext(mime)
        # Use modification time to create date folder
        try:
            mtime = time.localtime(path.stat().st_mtime)
            date = time.strftime('%Y.%m.%d', mtime)
        except Exception:
            date = 'unknown'
        dst_dir = out / date
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst_name = path.name + '.' + ext
        dst_path = dst_dir / dst_name
        # If destination exists, append a numeric suffix
        if dst_path.exists():
            base = dst_path.stem
            suffix = dst_path.suffix
            i = 1
            while True:
                candidate = dst_dir / f"{base}_{i}{suffix}"
                if not candidate.exists():
                    dst_path = candidate
                    break
                i += 1
        try:
            shutil.copy2(path, dst_path)
        except Exception as e:
            print(f"Copy failed: {path} -> {dst_path}: {e}")


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Recover KakaoTalk expired files by scanning a contents folder and adding extensions based on MIME signatures.')
    p.add_argument('-s', '--src', required=True, help='Path to the copied KakaoTalk contents folder')
    p.add_argument('-o', '--out', default='./result', help='Output folder for recovered files (default: ./result)')
    args = p.parse_args()
    process(args.src, args.out)
