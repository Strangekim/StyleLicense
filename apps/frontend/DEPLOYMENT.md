# Firebase Hosting 배포 가이드

StyleLicense 프론트엔드를 Firebase Hosting에 배포하는 방법을 안내합니다.

## 배포 환경

- **배포 플랫폼**: Firebase Hosting
- **프로젝트 ID**: `noted-sled-478700-r3`
- **배포 URL**: https://noted-sled-478700-r3.web.app
- **백엔드 API**: https://stylelicense-backend-606831968092.asia-northeast3.run.app

---

## 사전 준비 (최초 1회)

### 1. Firebase CLI 설치

```bash
# npm으로 전역 설치
npm install -g firebase-tools

# 설치 확인
firebase --version
```

### 2. Firebase 로그인

```bash
firebase login
```

브라우저가 열리면 Google 계정으로 로그인합니다.

### 3. Google OAuth Client ID 설정

`.env.production` 파일을 열어 실제 프로덕션 Google OAuth Client ID로 수정:

```env
# apps/frontend/.env.production
VITE_GOOGLE_CLIENT_ID=실제-클라이언트-ID로-변경
```

**Client ID 확인 방법**:
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 `noted-sled-478700-r3` 선택
3. APIs & Services → Credentials
4. OAuth 2.0 Client IDs에서 Web client 확인

**승인된 JavaScript 출처에 추가**:
```
https://noted-sled-478700-r3.web.app
```

**승인된 리디렉션 URI에 추가**:
```
https://noted-sled-478700-r3.web.app/auth/callback
```

---

## 배포 방법

### Option 1: NPM 스크립트 사용 (권장)

```bash
cd apps/frontend

# 빌드 + 배포 (한 번에)
npm run deploy:firebase
```

### Option 2: 단계별 수동 배포

```bash
cd apps/frontend

# 1. 프로덕션 빌드
npm run build:prod

# 2. 빌드 결과 확인
ls dist/

# 3. Firebase 배포
firebase deploy --only hosting
```

### 배포 성공 확인

배포가 완료되면 다음과 같은 메시지가 출력됩니다:

```
✔  Deploy complete!

Project Console: https://console.firebase.google.com/project/noted-sled-478700-r3/overview
Hosting URL: https://noted-sled-478700-r3.web.app
```

---

## 배포 후 확인사항

### 1. 웹사이트 접속 확인
```
https://noted-sled-478700-r3.web.app
```

### 2. 백엔드 API 연결 확인
- 브라우저 개발자 도구 → Network 탭
- API 요청이 `https://stylelicense-backend-606831968092.asia-northeast3.run.app`로 가는지 확인

### 3. Google OAuth 로그인 테스트
- 로그인 버튼 클릭
- Google 계정 선택
- 정상 로그인 확인

### 4. 페이지 로딩 성능 확인
- Chrome DevTools → Lighthouse
- Performance, Accessibility 점수 확인

---

## 롤백 (이전 버전으로 복구)

### Firebase Console에서 롤백

1. [Firebase Console](https://console.firebase.google.com/project/noted-sled-478700-r3/hosting) 접속
2. Hosting → 배포 기록 확인
3. 이전 버전 옆 "..." 메뉴 → "Roll back"

### CLI로 배포 기록 확인

```bash
firebase hosting:channel:list
```

---

## 문제 해결

### 1. "Error: HTTP Error: 403, The caller does not have permission"

**원인**: Firebase 권한 부족

**해결**:
```bash
# 다시 로그인
firebase logout
firebase login

# 프로젝트 확인
firebase projects:list
```

### 2. 배포 후 404 에러 (새로고침 시)

**원인**: SPA 라우팅 설정 누락

**해결**: `firebase.json`에 rewrite 규칙 확인
```json
{
  "rewrites": [
    {
      "source": "**",
      "destination": "/index.html"
    }
  ]
}
```

### 3. 환경 변수가 반영되지 않음

**원인**: 빌드 시 `.env.production` 파일을 읽지 못함

**해결**:
```bash
# .env.production 파일 존재 확인
ls -la apps/frontend/.env.production

# 빌드 시 환경 변수 명시적 전달
VITE_API_BASE_URL=https://stylelicense-backend-606831968092.asia-northeast3.run.app npm run build
```

### 4. Google OAuth 리디렉션 에러

**원인**: 승인된 리디렉션 URI 미등록

**해결**:
1. Google Cloud Console → APIs & Services → Credentials
2. OAuth Client ID 편집
3. 승인된 JavaScript 출처에 `https://noted-sled-478700-r3.web.app` 추가
4. 승인된 리디렉션 URI에 `https://noted-sled-478700-r3.web.app/auth/callback` 추가

---

## 비용 모니터링

Firebase Hosting 무료 티어 제한:
- **Storage**: 10GB
- **Data transfer**: 360MB/day (~10GB/month)

현재 사용량 확인:
1. [Firebase Console](https://console.firebase.google.com/project/noted-sled-478700-r3/usage) 접속
2. Usage and billing → Hosting 섹션 확인

---

## 추가 설정 (선택 사항)

### 커스텀 도메인 연결

나중에 `stylelicense.app` 같은 커스텀 도메인을 연결하려면:

```bash
firebase hosting:channel:deploy production --only hosting
```

Firebase Console → Hosting → Add custom domain

---

## 참고 자료

- [Firebase Hosting 공식 문서](https://firebase.google.com/docs/hosting)
- [Vite 환경 변수 가이드](https://vitejs.dev/guide/env-and-mode.html)
- [Vue Router History Mode](https://router.vuejs.org/guide/essentials/history-mode.html)
