#!/bin/bash
# ============================================================
# 갤러리 자동 갱신 스크립트
#
# 사용법:
#   1. images/full/ 폴더에서 사진(jpg)을 추가/삭제/이름변경
#      - 정렬은 파일명 오름차순 → 순서를 바꾸려면 파일명 숫자를 조정
#   2. ./update-gallery.sh 실행
#      - images/ 에 480px 썸네일 자동 생성/삭제
#      - index.html 의 갤러리 목록 자동 재생성 (처음 12장 노출)
#   3. 확인 후 커밋·푸시:
#      git add -A images index.html && git commit -m "갤러리 업데이트" && git push
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"

FULL_DIR="images/full"
THUMB_DIR="images"
VISIBLE=12

# ── 1) 썸네일 생성 (원본이 새로 추가/수정된 것만) ──
count=0
for src in "$FULL_DIR"/*.jpg "$FULL_DIR"/*.jpeg; do
  [ -e "$src" ] || continue
  name=$(basename "$src")
  dst="$THUMB_DIR/$name"
  if [ ! -f "$dst" ] || [ "$src" -nt "$dst" ]; then
    sips --resampleWidth 480 -s format jpeg -s formatOptions 68 "$src" --out "$dst" >/dev/null
    echo "  썸네일 생성: $name"
  fi
  count=$((count+1))
done

if [ "$count" -eq 0 ]; then
  echo "오류: $FULL_DIR 에 jpg 사진이 없습니다."
  exit 1
fi

# ── 2) 고아 썸네일 정리 (원본이 삭제된 썸네일 제거) ──
for thumb in "$THUMB_DIR"/*.jpg "$THUMB_DIR"/*.jpeg; do
  [ -e "$thumb" ] || continue
  name=$(basename "$thumb")
  # 갤러리 외 이미지(cover, parents 등)는 건드리지 않음
  case "$name" in
    cover*|parents*|invite*) continue ;;
  esac
  if [ ! -f "$FULL_DIR/$name" ]; then
    rm "$thumb"
    echo "  썸네일 삭제: $name (원본 없음)"
  fi
done

# ── 3) index.html 갤러리 목록 재생성 ──
python3 - "$VISIBLE" <<'PYEOF'
import os, re, sys

visible = int(sys.argv[1])
files = sorted(f for f in os.listdir('images/full') if re.search(r'\.jpe?g$', f, re.I))
lines = []
for i, f in enumerate(files, 1):
    cls = ' class="hidden-item"' if i > visible else ''
    lines.append(f'        <img{cls} src="images/{f}" data-full="images/full/{f}" '
                 f'loading="lazy" alt="웨딩 사진 {i}" onclick="openLightbox(this)">')

html = open('index.html', encoding='utf-8').read()
pattern = re.compile(r'(<!-- GALLERY:START -->).*?(\n\s*<!-- GALLERY:END -->)', re.S)
if not pattern.search(html):
    sys.exit('오류: index.html에서 GALLERY:START/END 마커를 찾지 못했습니다.')
html = pattern.sub(lambda m: m.group(1) + '\n' + '\n'.join(lines) + m.group(2), html)
open('index.html', 'w', encoding='utf-8').write(html)
print(f'완료: 사진 {len(files)}장 반영 (처음 {min(visible, len(files))}장 노출, 나머지 {max(0, len(files)-visible)}장은 더보기)')
PYEOF

echo ""
echo "다음 단계: 로컬에서 확인 후 아래 명령으로 배포하세요."
echo "  git add -A images index.html && git commit -m \"갤러리 업데이트\" && git push"
