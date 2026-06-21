# Mobile Wedding Invitation

SceneKoong 샘플 청첩장의 모바일 흐름을 참고해 만든 정적 샘플 사이트입니다.

## 구성

- 모바일 우선 커버/초대말/Save the Date/예식 안내/지도/갤러리/방명록/안내사항/계좌/RSVP/공유
- 모든 데이터 저장은 브라우저 `localStorage` 기반 샘플입니다.
- 실제 운영 시 RSVP와 방명록은 별도 백엔드나 Google Forms, Supabase, Firebase 등으로 연결하세요.

## GitHub Pages

이 저장소는 `.github/workflows/pages.yml` 워크플로를 통해 `main` 브랜치의 정적 파일을 GitHub Pages로 배포하도록 구성되어 있습니다.

## 카카오맵

`index.html`의 `<meta name="kakao-map-app-key" content="" />`에 Kakao Developers에서 발급한 JavaScript 키를 넣고, 허용 도메인에 `https://sumniy.github.io`를 등록하면 오시는 길 영역에 실제 카카오맵이 표시됩니다. 키가 비어 있거나 도메인이 허용되지 않으면 기존 지도 프리뷰가 표시됩니다.
