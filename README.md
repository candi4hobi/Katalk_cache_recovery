# KakaoTalk cache recovery
Recover file types from a copied KakaoTalk Android cache, then find a cached
original image from a screenshot of an expired preview.

## 1. Copy the cache from the phone
```powershell
adb version
adb devices # Unlock the phone and approve USB debugging if prompted.
adb pull /sdcard/Android/data/com.kakao.talk/contents "<CACHE_COPY_DIR>"
```
ADB creates `<CACHE_COPY_DIR>/contents`. The commands do not modify or delete
files on the phone.

## 2. Recover recognizable files
```powershell
conda create -n katalk python=3.8 -y
conda activate katalk
python -m pip install python-magic-bin tqdm pillow numpy
python recover.py --src "<CACHE_COPY_DIR>/contents" --out "<RECOVERED_OUTPUT_DIR>"
```
Recovered copies with inferred extensions are written to the output directory
you chose, organized into date folders.

## 3. Find an image from an expired preview
Crop the screenshot around the wanted image, then run:
```powershell
python find_kakao_preview.py "<REFERENCE_IMAGE_PATH>" "<RECOVERED_OUTPUT_DIR>" --out "<MATCH_RESULTS_DIR>" --top 80
```
Results:
- `<MATCH_RESULTS_DIR>/matches.csv`: candidate paths in similarity order.
- `<MATCH_RESULTS_DIR>/contact_sheet.jpg`: visual sheet of the top candidates.

The finder can compare previews that are darker than the original or contain
overlaid icons and text.