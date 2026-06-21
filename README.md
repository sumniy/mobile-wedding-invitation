# Mobile Wedding Invitation

VividVows 샘플 청첩장의 모바일 흐름을 참고해 만든 정적 샘플 사이트입니다.

## 구성

- 모바일 우선 커버/초대말/소개/일정/지도/갤러리/안내사항/계좌/RSVP/게스트앨범/공유
- 모든 데이터 저장은 브라우저 `localStorage` 기반 샘플입니다.
- 실제 운영 시 RSVP와 게스트앨범 업로드는 별도 백엔드나 Google Forms, Supabase, Firebase 등으로 연결하세요.

## 제외한 섹션

- 우리의 이야기
- 우리에게 물었습니다
- 우리가 함께한지
- 방명록

## GitHub Pages

이 저장소는 `.github/workflows/pages.yml` 워크플로를 통해 `main` 브랜치의 정적 파일을 GitHub Pages로 배포하도록 구성되어 있습니다.
