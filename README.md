# Katalk_cache_recovery

이 저장소는 블로그 글(카카오톡 저장기간 만료 파일 복구)을 참고해 카카오톡 앱의 임시 저장 폴더에 남아 있는 만료된(서버에서는 삭제된) 파일 조각을 찾아 실제 파일 확장자를 붙여 복구하는 간단한 도구와 설명을 제공합니다.

주의: 이 도구는 사용자가 자신의 기기에서 직접 접근 가능한 파일(예: Android/data/com.kakao.talk/contents)을 대상으로 합니다. Android 버전(특히 Android 11 이상)의 파일 접근 제약 때문에 루트 권한 또는 ADB 등의 방법으로 폴더를 추출해야 할 수 있습니다. 개인정보/저작권이 있는 파일을 무단으로 복구·배포하지 마십시오.

요약
- 원리: 카카오톡이 기기에 남겨둔 임시 파일들을 검사하여 파일 시그니처(매직 바이트)를 통해 MIME 타입을 판별하고 확장자를 붙여 복사합니다.
- 입력: 카카오톡의 contents(또는 앱이 저장한 캐시) 폴더를 PC로 복사한 경로
- 출력: 날짜별로 정리된 결과 디렉터리(확장자 추가된 파일들)

설치 및 사용법

1) 폴더 추출(PC로 복사)
- 파일 관리자 앱이나 USB, 또는 ADB를 사용해 Android 기기에서 contents 폴더를 PC로 복사합니다.
  예: adb를 통한 복사(기기와 권한에 따라 불가할 수 있음)

  adb pull /sdcard/Android/data/com.kakao.talk/contents ./kakao_contents

  참고: Android 11+에서는 /Android/data 폴더 접근이 제한됩니다. 이 경우 파일 관리자 앱의 내보내기(export) 기능이나 기기 루트 권한, 제조사 제공 백업 툴 등을 사용해야 할 수 있습니다.

2) 파이썬 의존성 설치

- 리눅스/맥
  pip3 install -r requirements.txt

- 윈도우
  pip install python-magic-bin tqdm

3) 실행 예시

  python3 recover.py -s ./kakao_contents -o ./result

결과는 ./result/연도.월.일/파일명.확장자 형태로 복사됩니다.

더 읽을거리
- 원글 블로그: https://bperhaps.tistory.com/entry/카카오톡-저장-기간-만료-파일-복구
- 관련 깃허브 예제: https://github.com/bperhaps/Recovering-KakaoTalk-Expired-Files

라이선스
- MIT License
