# Katalk_cache_recovery

This repository provides a small recovery tool and documentation based on a blog post about recovering KakaoTalk files whose download period has expired on the server. The tool scans temporary files left by the KakaoTalk app on a device, detects file types from signatures (magic bytes), assigns extensions, and copies files into a date-organized output directory.

Warning: This tool works on files that are accessible from your own device (for example, a copied Android/data/com.kakao.talk/contents folder). On Android 11+ access to Android/data may be restricted; you may need to extract the folder using ADB, a file manager export, or a device backup tool. Do not recover or redistribute files that you do not have the right to access.

Summary
- Principle: Scan the app's temporary files and determine file types using file signatures (MIME). Attach extensions and copy files into a structured output.
- Input: A local copy of the KakaoTalk contents (or cached) folder.
- Output: Files copied into a result directory organized by modification date, with inferred extensions.

Installation and usage

1) Extract the folder to your PC
- Copy the contents folder from your Android device to your PC using a file manager, USB, or ADB.
  Example (may require proper permissions):

  adb pull /sdcard/Android/data/com.kakao.talk/contents ./kakao_contents

  Note: Access to /Android/data is restricted on Android 11 and later. Use a file manager export, manufacturer backup tool, or obtain proper permissions if needed.

2) Install Python dependencies

- Linux/macOS
  pip3 install -r requirements.txt

- Windows
  pip install python-magic-bin tqdm

3) Run the recovery script

  python3 recover.py -s ./kakao_contents -o ./result

Results will be saved in ./result/YYYY.MM.DD/filename.extension

Further reading
- Original blog post: https://bperhaps.tistory.com/entry/%EC%B9%B4%EC%B9%B4%EC%98%A4%ED%86%A1-%EC%A0%80%EC%9E%A5-%EA%B8%B0%EA%B0%84-%EB%A7%8C%EB%A3%8C-%ED%8C%8C%EC%9D%BC-%EB%B3%B5%EA%B5%AC
- Reference repository: https://github.com/bperhaps/Recovering-KakaoTalk-Expired-Files

License
- MIT License
