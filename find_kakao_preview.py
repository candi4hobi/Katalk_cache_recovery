"""Find a cached image from a cropped/expired-preview screenshot.

The reference may be darker than the cache image and may have text or icons
drawn on it. The whole reference image is always compared: this tool makes no
assumption about where those overlays are. It runs completely locally.
"""

from __future__ import annotations

import argparse
import csv
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
# Large enough to preserve scene layout, small enough for a large cache scan.
COMPARE_WIDTH = 96


def comparison_size(reference_path: Path) -> tuple[int, int]:
    """Choose a small size with the cropped reference image's aspect ratio."""
    with Image.open(reference_path) as image:
        image = ImageOps.exif_transpose(image)
        aspect_ratio = image.width / image.height
    height = round(COMPARE_WIDTH / aspect_ratio)
    return COMPARE_WIDTH, max(24, min(192, height))


def normalized_image(path: Path, size: tuple[int, int]) -> np.ndarray:
    """Load an image as a small grayscale image with the target aspect ratio."""
    with Image.open(path) as image:
        # JPEG can often decode directly at a smaller native resolution.
        image.draft("L", (size[0] * 2, size[1] * 2))
        image = ImageOps.exif_transpose(image).convert("L")
        image = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.float32)


def pearson_similarity(first: np.ndarray, second: np.ndarray) -> float:
    """Compare structure while ignoring uniform brightness/contrast changes."""
    first = first - first.mean()
    second = second - second.mean()
    denominator = math.sqrt(float(np.dot(first.ravel(), first.ravel()) * np.dot(second.ravel(), second.ravel())))
    if denominator == 0:
        return -1.0
    return float(np.dot(first.ravel(), second.ravel()) / denominator)


def best_shift_similarity(reference: np.ndarray, candidate: np.ndarray, maximum_shift: int) -> float:
    """Best whole-image correlation across small x/y translations.

    No region is masked or excluded. At a non-zero shift, only the naturally
    overlapping rectangle is compared, reducing the effect of a slightly
    different user crop position.
    """
    height, width = reference.shape
    best = -1.0
    for y_shift in range(-maximum_shift, maximum_shift + 1):
        y_ref_start, y_ref_end = max(0, y_shift), min(height, height + y_shift)
        y_cand_start, y_cand_end = max(0, -y_shift), min(height, height - y_shift)
        for x_shift in range(-maximum_shift, maximum_shift + 1):
            x_ref_start, x_ref_end = max(0, x_shift), min(width, width + x_shift)
            x_cand_start, x_cand_end = max(0, -x_shift), min(width, width - x_shift)
            score = pearson_similarity(
                reference[y_ref_start:y_ref_end, x_ref_start:x_ref_end],
                candidate[y_cand_start:y_cand_end, x_cand_start:x_cand_end],
            )
            best = max(best, score)
    return best


def score_one(path: Path, reference: np.ndarray, size: tuple[int, int], maximum_shift: int) -> tuple[float, Path] | None:
    try:
        return best_shift_similarity(reference, normalized_image(path, size), maximum_shift), path
    except (OSError, UnidentifiedImageError, ValueError):
        return None


def make_contact_sheet(rows: list[tuple[float, Path]], output: Path) -> None:
    cell_width, cell_height, columns = 250, 210, 5
    thumb_size = (230, 172)
    sheet = Image.new("RGB", (columns * cell_width, math.ceil(len(rows) / columns) * cell_height), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, (score, path) in enumerate(rows):
        x, y = (index % columns) * cell_width, (index // columns) * cell_height
        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                image = ImageOps.fit(image, thumb_size, method=Image.Resampling.LANCZOS)
            sheet.paste(image, (x + 10, y + 6))
            draw.text((x + 10, y + 183), f"#{index + 1}  {score:.4f}  {path.name}"[:42], fill="black", font=font)
        except (OSError, UnidentifiedImageError):
            pass
    sheet.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rank cache images by similarity to a cropped expired-preview screenshot."
    )
    parser.add_argument("reference", type=Path, help="Cropped screenshot of the wanted image")
    parser.add_argument("input_dir", type=Path, help="Directory containing cache images (searched recursively)")
    parser.add_argument("--out", type=Path, default=Path("cache_matches"), help="Output folder (default: cache_matches)")
    parser.add_argument("--top", type=int, default=60, help="Number of ranked candidates to save (default: 60)")
    parser.add_argument("--shift", type=int, default=2, help="Maximum comparison-image translation in pixels (default: 2; 0 is strict)")
    parser.add_argument("--workers", type=int, default=4, help="Parallel readers (default: 4; use 2 for a spinning external HDD)")
    args = parser.parse_args()

    if args.shift < 0 or args.top < 1 or args.workers < 1:
        parser.error("--shift must be >= 0; --top and --workers must be >= 1")
    if not args.reference.is_file():
        parser.error(f"reference image was not found: {args.reference}")
    if not args.input_dir.is_dir():
        parser.error(f"input directory was not found: {args.input_dir}")

    args.out.mkdir(parents=True, exist_ok=True)
    size = comparison_size(args.reference)
    reference = normalized_image(args.reference, size)
    # Avoid a slow individual is_file() call on archive/external volumes. Any
    # directory with an image-like suffix is safely skipped by score_one.
    files = [path for path in args.input_dir.rglob("*") if path.suffix.lower() in IMAGE_EXTENSIONS]
    print(f"Found {len(files):,} image files to scan.", flush=True)

    matches: list[tuple[float, Path]] = []
    skipped = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for index, result in enumerate(pool.map(lambda path: score_one(path, reference, size, args.shift), files), 1):
            if result is None:
                skipped += 1
            else:
                matches.append(result)
            if index % 100 == 0 or index == len(files):
                print(f"scanned {index:,}/{len(files):,}", flush=True)

    matches.sort(key=lambda item: item[0], reverse=True)
    top = matches[: args.top]
    with (args.out / "matches.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["rank", "similarity", "path"])
        for rank, (score, path) in enumerate(top, 1):
            writer.writerow([rank, f"{score:.6f}", str(path)])
    make_contact_sheet(top, args.out / "contact_sheet.jpg")
    print(f"\nWrote {len(top)} candidates to {args.out.resolve()}")
    print(f"Unreadable files skipped: {skipped}")
    if top:
        print(f"Best match: {top[0][0]:.6f}  {top[0][1]}")


if __name__ == "__main__":
    main()
