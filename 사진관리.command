#!/bin/bash
# Finder에서 더블클릭하면 사진 관리 화면이 브라우저로 열립니다.
cd "$(dirname "$0")"
python3 tools/photo_admin.py
