#!/usr/bin/env python3
"""
recover.py

카카오톡의 contents 폴더(또는 앱이 남긴 임시 파일들)를 스캔하여 매직 바이트(MIME)를 기반으로 확장자를 붙이고 날짜별로 정리해 복사합니다.

사용법:
  python3 recover.py -s /path/to/contents -o ./result

필수: python-magic (또는 windows에서 python-magic-bin)
"""

import os
import time
import shutil
import argparse
import mimetypes
from pathlib import Path

try:
    import magic
except Exception as e:
    print("python-magic 모듈을 찾을 수 없습니다. 설치: pip install python-magic (또는 Windows: python-magic-bin)")
    raise

from tqdm import tqdm

# 간단한 MIME -> 확장자 보정 매핑
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
    # mimetypes에서 확장자를 추측
    try:
        ext = mimetypes.guess_extension(mime)
    except Exception:
        ext = None
    if ext:
        return ext.lstrip('.')
    # fallback map
    if mime in FALLBACK_MAP:
        return FALLBACK_MAP[mime]
    # 마지막 수단: 슬래시 뒤를 사용
    if '/' in mime:
        return mime.split('/')[-1]
    return 'bin'


def process(src_dir: str, out_dir: str, follow_symlinks: bool = False):
    src = Path(src_dir)
    out = Path(out_dir)
    if not src.exists():
        raise FileNotFoundError(f"소스 폴더를 찾을 수 없습니다: {src}")
    out.mkdir(parents=True, exist_ok=True)

    # magic 객체 생성
    mg = magic.Magic(mime=True)

    # 파일 개수 세기
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
        # 파일 수정 시간을 기준으로 날짜별 폴더
        try:
            mtime = time.localtime(path.stat().st_mtime)
            date = time.strftime('%Y.%m.%d', mtime)
        except Exception:
            date = 'unknown'
        dst_dir = out / date
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst_name = path.name + '.' + ext
        dst_path = dst_dir / dst_name
        # 같은 이름 존재시 숫자 붙이기
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
            print(f"복사 실패: {path} -> {dst_path}: {e}")


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Recover KakaoTalk expired files by scanning contents folder and adding extensions based on MIME signatures.')
    p.add_argument('-s', '--src', required=True, help='카카오톡 contents 폴더를 복사해 둔 경로')
    p.add_argument('-o', '--out', default='./result', help='복구 결과를 저장할 폴더 (기본: ./result)')
    args = p.parse_args()
    process(args.src, args.out)
