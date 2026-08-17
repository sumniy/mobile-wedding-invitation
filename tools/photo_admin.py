#!/usr/bin/env python3
# ============================================================
# 갤러리 사진 관리 서버
#
# 실행:  저장소 루트의 '사진관리.command' 더블클릭
#        (또는 터미널에서 python3 tools/photo_admin.py)
#
# 브라우저에 관리 화면(http://localhost:8765/admin)이 열립니다.
#   - 사진 드래그앤드롭/선택으로 추가 (jpg·png·heic 자동 변환)
#   - 삭제 · ◀▶ 순서 변경
#   - 오른쪽에서 실제 청첩장 실시간 미리보기
#   - '배포하기' 버튼 → 커밋·푸시·반영 확인까지 자동
#
# 사진 원본은 images/full/, 썸네일·HTML 갱신은 update-gallery.sh 재사용.
# 파일명은 변경될 때마다 gallery-01.. 순번으로 자동 정리됩니다.
# ============================================================
import base64
import http.server
import json
import os
import re
import subprocess
import sys
import threading
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL = os.path.join(ROOT, 'images', 'full')
os.chdir(ROOT)

PORTS = [8765, 8766, 8767, 8768]


def list_photos():
    return sorted(f for f in os.listdir(FULL) if re.search(r'\.jpe?g$', f, re.I))


def normalize(order):
    """order(현재 파일명들의 원하는 순서)대로 gallery-01.. 로 2단계 rename.
    썸네일도 같은 이름으로 함께 이동해 원본-썸네일 짝이 어긋나지 않게 유지."""
    thumbs_dir = os.path.join(ROOT, 'images')
    tmps = []
    for i, name in enumerate(order, 1):
        tmp = os.path.join(FULL, f'__tmp__{i:03d}.jpg')
        os.rename(os.path.join(FULL, name), tmp)
        thumb = os.path.join(thumbs_dir, name)
        tmp_thumb = os.path.join(thumbs_dir, f'__tmp__{i:03d}.jpg')
        os.rename(thumb, tmp_thumb) if os.path.isfile(thumb) else None
        tmps.append((tmp, tmp_thumb if os.path.isfile(tmp_thumb) else None))
    for i, (tmp, tmp_thumb) in enumerate(tmps, 1):
        os.rename(tmp, os.path.join(FULL, f'gallery-{i:02d}.jpg'))
        if tmp_thumb:
            os.rename(tmp_thumb, os.path.join(thumbs_dir, f'gallery-{i:02d}.jpg'))


def run_update(deploy=False):
    cmd = ['./update-gallery.sh'] + ([] if deploy else ['--no-deploy'])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600 if deploy else 180)
    return r.returncode == 0, (r.stdout + r.stderr)


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip('/') == '/admin':
            body = ADMIN_HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.startswith('/api/list'):
            self._json({'photos': list_photos()})
            return
        super().do_GET()

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        try:
            data = json.loads(self.rfile.read(n) or b'{}')
        except json.JSONDecodeError:
            self._json({'ok': False, 'log': '잘못된 요청'}, 400)
            return
        try:
            if self.path == '/api/upload':
                before = list_photos()
                raw = base64.b64decode(data['data'])
                ext = os.path.splitext(data.get('name', ''))[1].lower()
                incoming = os.path.join(FULL, '__incoming__.jpg')
                if os.path.exists(incoming):
                    os.remove(incoming)
                if ext in ('.jpg', '.jpeg'):
                    with open(incoming, 'wb') as f:
                        f.write(raw)
                else:  # png·heic 등 → sips로 jpg 변환
                    tmp = os.path.join(FULL, '__incoming_src__' + (ext or '.bin'))
                    with open(tmp, 'wb') as f:
                        f.write(raw)
                    subprocess.run(
                        ['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '88',
                         tmp, '--out', incoming],
                        check=True, capture_output=True)
                    os.remove(tmp)
                normalize(before + ['__incoming__.jpg'])
                ok, out = run_update(False)
                self._json({'ok': ok, 'log': out})

            elif self.path == '/api/delete':
                name = os.path.basename(data['name'])
                target = os.path.join(FULL, name)
                if not os.path.isfile(target):
                    self._json({'ok': False, 'log': '파일 없음: ' + name}, 404)
                    return
                os.remove(target)
                thumb = os.path.join(ROOT, 'images', name)
                if os.path.isfile(thumb):
                    os.remove(thumb)
                normalize(list_photos())
                ok, out = run_update(False)
                self._json({'ok': ok, 'log': out})

            elif self.path == '/api/order':
                names = [os.path.basename(x) for x in data['names']]
                if sorted(names) != list_photos():
                    self._json({'ok': False, 'log': '목록이 서버와 달라요. 새로고침 후 다시 시도하세요.'}, 409)
                    return
                normalize(names)
                ok, out = run_update(False)
                self._json({'ok': ok, 'log': out})

            elif self.path == '/api/deploy':
                ok, out = run_update(True)
                self._json({'ok': ok, 'log': out})

            else:
                self._json({'ok': False, 'log': '알 수 없는 요청'}, 404)
        except Exception as e:  # noqa: BLE001 - 관리 도구: 모든 실패를 화면에 그대로 보여줌
            self._json({'ok': False, 'log': str(e)}, 500)


ADMIN_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>청첩장 사진 관리</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Apple SD Gothic Neo', sans-serif; background: #F5F0E6; color: #4A4139; height: 100vh; display: flex; flex-direction: column; }
  header { display: flex; align-items: center; gap: 14px; padding: 14px 20px; background: #FFFDF8; border-bottom: 1px solid #E0D6C4; }
  header h1 { font-size: 17px; }
  header .count { color: #8C7C64; font-size: 13px; }
  #status { margin-left: auto; font-size: 13px; color: #8C7C64; max-width: 45%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  #deploy { padding: 10px 22px; border: 0; background: #8C7C64; color: #fff; font-size: 14px; border-radius: 6px; cursor: pointer; }
  #deploy:disabled { opacity: .5; }
  main { flex: 1; display: flex; min-height: 0; }
  #left { flex: 1; overflow-y: auto; padding: 16px; }
  #drop {
    border: 2px dashed #C7B99F; border-radius: 10px; padding: 22px; text-align: center;
    color: #8C7C64; font-size: 14px; margin-bottom: 14px; cursor: pointer; background: #FBF8F2;
  }
  #drop.hover { background: #F1EADD; border-color: #8C7C64; }
  #grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }
  .card { position: relative; background: #fff; border: 1px solid #E0D6C4; border-radius: 8px; overflow: hidden; cursor: grab; }
  .card.dragging { opacity: .35; }
  .card.ins-b { box-shadow: -4px 0 0 0 #8C7C64; }
  .card.ins-a { box-shadow: 4px 0 0 0 #8C7C64; }
  .card img { display: block; width: 100%; aspect-ratio: 1; object-fit: cover; object-position: center 22%; pointer-events: none; }
  .card .no { position: absolute; top: 6px; left: 6px; background: rgba(74,65,57,.85); color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 10px; cursor: pointer; }
  .card .no:hover { background: #8C7C64; }
  .card .bar { display: flex; }
  .card .bar button { flex: 1; padding: 8px 0; border: 0; background: #FBF8F2; cursor: pointer; font-size: 13px; color: #6B5C48; }
  .card .bar button:hover { background: #F1EADD; }
  .card .bar .del { color: #B0533D; }
  #right { width: 397px; border-left: 1px solid #E0D6C4; background: #EDE2CB; display: flex; flex-direction: column; }
  #right .cap { text-align: center; font-size: 12px; color: #8C7C64; padding: 8px; }
  #frame { flex: 1; border: 0; width: 375px; margin: 0 11px 11px; background: #fff; box-shadow: 0 2px 14px rgba(0,0,0,.12); }
  @media (max-width: 900px) { #right { display: none; } }
  /* 확대 뷰어 */
  #viewer { display: none; position: fixed; inset: 0; z-index: 50; background: rgba(40,34,28,.94); flex-direction: column; align-items: center; justify-content: center; }
  #viewer.open { display: flex; }
  #viewer img { max-width: 92%; max-height: 78vh; object-fit: contain; box-shadow: 0 8px 40px rgba(0,0,0,.5); }
  #viewer .vbar { margin-top: 16px; display: flex; gap: 10px; align-items: center; }
  #viewer .vbar button { padding: 10px 18px; border: 0; border-radius: 6px; background: #FBF8F2; color: #4A4139; font-size: 14px; cursor: pointer; }
  #viewer .vbar .vdel { background: #B0533D; color: #fff; }
  #viewer #vcount { color: #F5F0E6; font-size: 14px; min-width: 70px; text-align: center; }
  #viewer .vhint { margin-top: 10px; color: rgba(245,240,230,.6); font-size: 12px; }
</style>
</head>
<body>
<header>
  <h1>청첩장 사진 관리</h1>
  <span class="count" id="count"></span>
  <span id="status"></span>
  <button id="deploy" onclick="deploy()">배포하기</button>
</header>
<main>
  <div id="left">
    <div id="drop">여기로 사진을 끌어다 놓거나 클릭해서 선택하세요 (jpg·png·heic)<br>
      <small>순서 변경: 사진을 끌어서 원하는 자리에 놓기 · 번호를 누르면 원하는 위치로 바로 이동</small></div>
    <input type="file" id="file" accept=".jpg,.jpeg,.png,.heic" multiple hidden>
    <div id="grid"></div>
  </div>
  <div id="right">
    <div class="cap">실시간 미리보기 (변경 시 자동 새로고침)</div>
    <iframe id="frame" src="/"></iframe>
  </div>
</main>
<div id="viewer">
  <img id="vimg" alt="">
  <div class="vbar">
    <button onclick="viewerNav(-1)">◀ 이전</button>
    <span id="vcount"></span>
    <button onclick="viewerNav(1)">다음 ▶</button>
    <button class="vdel" onclick="viewerDel()">이 사진 삭제</button>
    <button onclick="closeViewer()">닫기</button>
  </div>
  <div class="vhint">사진을 클릭하면 원본 크기로 볼 수 있어요 · 키보드 ← → 이동, ESC 닫기</div>
</div>
<script>
let photos = [];
let busy = false;
let dragIdx = null;
let dropTarget = null; // { idx, before }
let justDragged = false;
let viewIdx = null;
const $ = (id) => document.getElementById(id);

function setStatus(msg) { $('status').textContent = msg || ''; }

function clearInsertMarks() {
  document.querySelectorAll('.card.ins-b, .card.ins-a').forEach(c => c.classList.remove('ins-b', 'ins-a'));
}

async function refresh(reloadFrame) {
  const r = await fetch('/api/list');
  photos = (await r.json()).photos;
  $('count').textContent = '총 ' + photos.length + '장 (처음 12장 노출)';
  const grid = $('grid');
  grid.innerHTML = '';
  photos.forEach((name, i) => {
    const card = document.createElement('div');
    card.className = 'card';
    card.draggable = true;
    card.innerHTML =
      '<img src="/images/' + name + '?v=' + Date.now() + '" loading="lazy" draggable="false">' +
      '<span class="no" title="눌러서 원하는 위치로 이동">' + (i + 1) + '</span>' +
      '<div class="bar">' +
        '<button ' + (i === 0 ? 'disabled' : '') + '>◀</button>' +
        '<button class="del">삭제</button>' +
        '<button ' + (i === photos.length - 1 ? 'disabled' : '') + '>▶</button>' +
      '</div>';
    const [prev, del_, next] = card.querySelectorAll('.bar button');
    prev.onclick = () => move(i, -1);
    next.onclick = () => move(i, 1);
    del_.onclick = () => del(i);
    card.querySelector('.no').onclick = () => jump(i);

    // 드래그로 순서 변경
    card.addEventListener('dragstart', (e) => {
      dragIdx = i;
      card.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', String(i)); // 파이어폭스 호환
    });
    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      clearInsertMarks();
      dragIdx = null; dropTarget = null;
      justDragged = true;
      setTimeout(() => { justDragged = false; }, 80);
    });
    // 카드(사진 영역) 클릭 → 확대 뷰어
    card.addEventListener('click', (e) => {
      if (justDragged) return;
      if (e.target.closest('.bar') || e.target.closest('.no')) return;
      openViewer(i);
    });
    card.addEventListener('dragover', (e) => {
      if (dragIdx === null || dragIdx === i) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const rect = card.getBoundingClientRect();
      const before = (e.clientX - rect.left) < rect.width / 2;
      if (!dropTarget || dropTarget.idx !== i || dropTarget.before !== before) {
        clearInsertMarks();
        card.classList.add(before ? 'ins-b' : 'ins-a');
        dropTarget = { idx: i, before };
      }
    });
    card.addEventListener('drop', async (e) => {
      e.preventDefault();
      if (dragIdx === null || !dropTarget) return;
      const from = dragIdx;
      let insertAt = dropTarget.idx + (dropTarget.before ? 0 : 1);
      clearInsertMarks();
      if (insertAt === from || insertAt === from + 1) return; // 제자리
      const names = photos.slice();
      const [item] = names.splice(from, 1);
      if (from < insertAt) insertAt--;
      names.splice(insertAt, 0, item);
      await api('/api/order', { names }, '순서 변경 중...');
    });
    grid.appendChild(card);
  });
  if (reloadFrame) $('frame').src = '/?t=' + Date.now();
}

async function api(path, body, busyMsg) {
  if (busy) return false;
  busy = true;
  setStatus(busyMsg);
  try {
    const r = await fetch(path, { method: 'POST', body: JSON.stringify(body || {}) });
    const data = await r.json();
    if (!data.ok) { alert('실패: ' + (data.log || '알 수 없는 오류')); setStatus('오류'); }
    else setStatus('완료');
    await refresh(true);
    return data.ok;
  } finally {
    busy = false;
  }
}

async function move(i, dir) {
  const names = photos.slice();
  const [item] = names.splice(i, 1);
  names.splice(i + dir, 0, item);
  await api('/api/order', { names }, '순서 변경 중...');
}

async function jump(i) {
  const v = prompt('몇 번째 위치로 이동할까요? (1~' + photos.length + ')', String(i + 1));
  if (v === null) return;
  const pos = parseInt(v, 10);
  if (!pos || pos < 1 || pos > photos.length) { alert('1~' + photos.length + ' 사이 숫자를 입력하세요.'); return; }
  if (pos - 1 === i) return;
  const names = photos.slice();
  const [item] = names.splice(i, 1);
  names.splice(pos - 1, 0, item);
  await api('/api/order', { names }, pos + '번째로 이동 중...');
}

async function del(i) {
  if (!confirm((i + 1) + '번 사진을 뺄까요? (원본 파일이 삭제됩니다)')) return;
  await api('/api/delete', { name: photos[i] }, '삭제 중...');
}

// ── 확대 뷰어 (원본 화질) ──
function openViewer(i) {
  viewIdx = i;
  renderViewer();
  $('viewer').classList.add('open');
}
function renderViewer() {
  if (viewIdx === null || !photos.length) return;
  $('vimg').src = '/images/full/' + photos[viewIdx] + '?v=' + Date.now();
  $('vcount').textContent = (viewIdx + 1) + ' / ' + photos.length;
}
function closeViewer() {
  $('viewer').classList.remove('open');
  viewIdx = null;
}
function viewerNav(d) {
  if (viewIdx === null) return;
  viewIdx = (viewIdx + d + photos.length) % photos.length;
  renderViewer();
}
async function viewerDel() {
  if (viewIdx === null) return;
  const i = viewIdx;
  if (!confirm((i + 1) + '번 사진을 뺄까요? (원본 파일이 삭제됩니다)')) return;
  const ok = await api('/api/delete', { name: photos[i] }, '삭제 중...');
  if (ok && photos.length) { viewIdx = Math.min(i, photos.length - 1); renderViewer(); }
  else closeViewer();
}
$('viewer').addEventListener('click', (e) => { if (e.target.id === 'viewer') closeViewer(); });
document.addEventListener('keydown', (e) => {
  if (!$('viewer').classList.contains('open')) return;
  if (e.key === 'Escape') closeViewer();
  else if (e.key === 'ArrowLeft') viewerNav(-1);
  else if (e.key === 'ArrowRight') viewerNav(1);
});

// 페이지 밖 드롭으로 브라우저가 이미지를 열어버리는 것 방지
document.addEventListener('dragover', (e) => e.preventDefault());
document.addEventListener('drop', (e) => e.preventDefault());

async function uploadFiles(files) {
  if (busy) { alert('이전 작업이 끝난 뒤 다시 시도하세요.'); return; }
  busy = true;
  try {
  for (const f of files) {
    setStatus(f.name + ' 추가 중...');
    const b64 = await new Promise((res) => {
      const rd = new FileReader();
      rd.onload = () => res(rd.result.split(',')[1]);
      rd.readAsDataURL(f);
    });
    const r = await fetch('/api/upload', { method: 'POST', body: JSON.stringify({ name: f.name, data: b64 }) });
    const data = await r.json();
    if (!data.ok) alert(f.name + ' 추가 실패: ' + (data.log || ''));
  }
  setStatus('완료');
  await refresh(true);
  } finally {
    busy = false;
  }
}

async function deploy() {
  if (!confirm('현재 상태로 실제 청첩장에 배포할까요?')) return;
  $('deploy').disabled = true;
  setStatus('배포 중... (최대 3분)');
  try {
    const r = await fetch('/api/deploy', { method: 'POST', body: '{}' });
    const data = await r.json();
    if (data.ok && data.log.includes('배포 완료')) setStatus('배포 완료!');
    else if (data.ok && data.log.includes('변경사항이 없어')) setStatus('변경사항 없음');
    else { setStatus('배포 확인 실패 — 로그 확인'); alert(data.log); }
  } catch (e) { setStatus('배포 오류'); alert(e); }
  $('deploy').disabled = false;
}

const drop = $('drop');
drop.onclick = () => $('file').click();
$('file').onchange = (e) => { uploadFiles([...e.target.files]); e.target.value = ''; };
drop.ondragover = (e) => { e.preventDefault(); drop.classList.add('hover'); };
drop.ondragleave = () => drop.classList.remove('hover');
drop.ondrop = (e) => {
  e.preventDefault();
  drop.classList.remove('hover');
  uploadFiles([...e.dataTransfer.files].filter(f => /\\.(jpe?g|png|heic)$/i.test(f.name)));
};

refresh(false);
</script>
</body>
</html>
"""


def main():
    port = None
    server = None
    for p in PORTS:
        try:
            server = http.server.ThreadingHTTPServer(('127.0.0.1', p), Handler)
            port = p
            break
        except OSError:
            continue
    if server is None:
        print('포트를 열 수 없습니다 (8765~8768 모두 사용 중).')
        sys.exit(1)

    url = f'http://localhost:{port}/admin'
    print('사진 관리 화면:', url)
    print('종료: Ctrl+C (이 창을 닫아도 됩니다)')
    if '--no-open' not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
