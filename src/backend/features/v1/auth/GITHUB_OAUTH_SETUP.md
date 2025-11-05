# GitHub OAuth 로그인 설정 가이드

## 1. GitHub OAuth App 생성

### 단계별 가이드:

1. **GitHub 웹사이트 접속**
   - https://github.com/settings/developers

2. **OAuth Apps 메뉴 선택**
   - Settings → Developer settings → OAuth Apps

3. **New OAuth App 클릭**

4. **애플리케이션 정보 입력**
   ```
   Application name: Sesami - GitHub Analyzer
   Homepage URL: http://localhost:3000
   Application description: GitHub contribution analyzer (선택사항)
   Authorization callback URL: http://localhost:3000/auth/callback
   ```

5. **Register application 클릭**

6. **Client ID와 Client Secret 복사**
   - Client ID: 즉시 표시됨
   - Client Secret: "Generate a new client secret" 클릭 후 복사

---

## 2. 환경 변수 설정

`.env` 파일에 GitHub OAuth 정보 입력:

```bash
# GitHub OAuth Configuration
GITHUB_CLIENT_ID=your_actual_client_id_here
GITHUB_CLIENT_SECRET=your_actual_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:3000/auth/callback
```

⚠️ **중요**:
- Client Secret은 절대 Git에 커밋하지 마세요!
- `.env` 파일이 `.gitignore`에 포함되어 있는지 확인하세요.

---

## 3. API 엔드포인트

### A. GitHub 로그인 URL 받기
```http
GET /api/v1/auth/github/login

Response:
{
  "authorization_url": "https://github.com/login/oauth/authorize?client_id=..."
}
```

### B. GitHub 콜백 처리 (코드 → JWT 토큰)
```http
POST /api/v1/auth/github/callback
Content-Type: application/json

{
  "code": "github_authorization_code_here"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "github_id": "12345678",
    "username": "octocat",
    "email": "octocat@github.com",
    "avatar_url": "https://avatars.githubusercontent.com/u/583231",
    "created_at": "2025-01-01T00:00:00"
  }
}
```

### C. 현재 사용자 정보 조회
```http
GET /api/v1/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Response:
{
  "id": 1,
  "github_id": "12345678",
  "username": "octocat",
  "email": "octocat@github.com",
  "avatar_url": "https://avatars.githubusercontent.com/u/583231",
  "created_at": "2025-01-01T00:00:00"
}
```

### D. 로그아웃
```http
POST /api/v1/auth/logout

Response:
{
  "message": "Successfully logged out"
}
```

---

## 4. 인증 플로우

```
1. 사용자가 "GitHub 로그인" 버튼 클릭
   ↓
2. 프론트엔드: GET /api/v1/auth/github/login
   ↓
3. 프론트엔드: 받은 URL로 리다이렉트 (GitHub 로그인 페이지)
   ↓
4. 사용자가 GitHub에서 권한 승인
   ↓
5. GitHub → 프론트엔드: code 파라미터와 함께 콜백 URL로 리다이렉트
   ↓
6. 프론트엔드: POST /api/v1/auth/github/callback { code }
   ↓
7. 백엔드: JWT 토큰 발급
   ↓
8. 프론트엔드: JWT 토큰을 localStorage에 저장
   ↓
9. 이후 모든 API 요청에 토큰 포함: Authorization: Bearer <token>
```

---

## 5. 보호된 엔드포인트 사용 예시

### Python/FastAPI
```python
from fastapi import Depends
from common.dependencies import get_current_user
from features.v1.auth.models import User

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}!"}
```

### cURL 테스트
```bash
# 1. GitHub 로그인 URL 받기
curl http://localhost:8000/api/v1/auth/github/login

# 2. 브라우저에서 URL 접속 → code 받기

# 3. 콜백으로 JWT 토큰 받기
curl -X POST http://localhost:8000/api/v1/auth/github/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "your_github_code_here"}'

# 4. JWT 토큰으로 보호된 엔드포인트 접근
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer your_jwt_token_here"
```

---

## 6. 프론트엔드 통합 (React 예시)

### A. 로그인 버튼
```typescript
// LoginPage.tsx
const handleGitHubLogin = async () => {
  const response = await fetch('http://localhost:8000/api/v1/auth/github/login');
  const data = await response.json();

  // GitHub 로그인 페이지로 리다이렉트
  window.location.href = data.authorization_url;
};

return <button onClick={handleGitHubLogin}>GitHub로 로그인</button>;
```

### B. 콜백 페이지
```typescript
// AuthCallbackPage.tsx
useEffect(() => {
  const handleCallback = async () => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');

    if (code) {
      const response = await fetch('http://localhost:8000/api/v1/auth/github/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
      });

      const data = await response.json();

      // JWT 토큰 저장
      localStorage.setItem('access_token', data.access_token);

      // 홈으로 리다이렉트
      window.location.href = '/';
    }
  };

  handleCallback();
}, []);
```

### C. API 요청에 토큰 자동 추가
```typescript
// api.ts
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1'
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

---

## 7. 트러블슈팅

### Q: "Invalid GitHub access token" 오류
**A**: GitHub Client ID/Secret이 올바른지 확인하세요.

### Q: "Token missing user identifier" 오류
**A**: JWT 토큰이 올바르게 생성되었는지 확인하세요.

### Q: CORS 오류
**A**: `config.py`의 `FRONTEND_URL`이 올바르게 설정되었는지 확인하세요.

### Q: 토큰 만료
**A**: 기본 만료 시간은 30분입니다. `.env`의 `ACCESS_TOKEN_EXPIRE_MINUTES`로 변경 가능합니다.

---

## 8. 보안 권장사항

✅ **DO**
- HTTPS 사용 (프로덕션)
- Client Secret은 백엔드에서만 사용
- JWT Secret Key 강력하게 설정 (32자 이상)
- 토큰 만료 시간 설정
- `.env` 파일 Git 커밋 금지

❌ **DON'T**
- Client Secret을 프론트엔드에 노출
- JWT Secret을 코드에 하드코딩
- 만료되지 않는 토큰 사용
- HTTP로 토큰 전송 (프로덕션)

---

## 9. 프로덕션 배포시 변경사항

`.env` 파일:
```bash
# 프로덕션 URL로 변경
FRONTEND_URL=https://yourdomain.com
GITHUB_REDIRECT_URI=https://yourdomain.com/auth/callback

# 강력한 Secret Key 생성
SECRET_KEY=$(openssl rand -hex 32)
```

GitHub OAuth App 설정도 프로덕션 URL로 업데이트 필요!
