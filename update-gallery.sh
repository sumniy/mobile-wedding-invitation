#!/bin/bash
# ============================================================
# 갤러리 자동 갱신 스크립트
#
# 사용법:
#   1. images/full/ 폴더에서 사진(jpg)을 추가/삭제/이름변경
#      - 정렬은 파일명 오름차순 → 순서를 바꾸려면 파일명 숫자를 조정
#   2. ./update-gallery.sh 실행 — 아래를 한 번에 처리
#      - images/ 에 480px 썸네일 자동 생성/삭제
#      - index.html 의 갤러리 목록 자동 재생성 (처음 12장 노출)
#      - 커밋 & 푸시 & 배포 완료 확인까지 자동
#
#   배포 없이 파일만 갱신하려면:  ./update-gallery.sh --no-deploy
#   주의: index.html에 다른 수정사항이 있으면 함께 커밋됩니다.
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

# ── 4) 커밋 & 푸시 & 배포 확인 ──
if [ "${1:-}" = "--no-deploy" ]; then
  echo ""
  echo "(--no-deploy) 파일만 갱신했습니다. 배포하려면 다시 실행하거나 직접 git push 하세요."
  exit 0
fi

git add index.html images
if git diff --cached --quiet; then
  echo ""
  echo "변경사항이 없어 배포를 생략합니다."
  exit 0
fi

git commit -m "갤러리 업데이트"
git push origin main
echo ""
echo "GitHub Pages 배포 대기 중 (보통 30초~2분)..."

LIVE_URL="https://sumniy.github.io/mobile-wedding-invitation/"
local_sig=$(grep -o 'data-full="images/full/[^"]*"' index.html | md5 -q)
for i in $(seq 1 9); do
  sleep 20
  live_sig=$(curl -sf "$LIVE_URL" | grep -o 'data-full="images/full/[^"]*"' | md5 -q || true)
  if [ "$live_sig" = "$local_sig" ]; then
    echo "배포 완료! 확인: $LIVE_URL"
    exit 0
  fi
  echo "  아직 반영 전... ($i/9)"
done
echo "3분 내 반영 확인에 실패했습니다. 잠시 후 직접 확인해 보세요: $LIVE_URL"
