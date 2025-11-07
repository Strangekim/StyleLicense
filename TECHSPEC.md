# Style License 프로젝트 기술 명세서 (TECHSPEC.md)

**Repository :**  작성 예정
**Version :** 1.0

---

## 목차
1. [프로젝트 개요](#1-프로젝트-개요)
2. [목표 및 비목표](#2-목표-및-비목표)
3. [배경 및 문제 정의](#3-배경-및-문제-정의)
4. [시스템 아키텍처](#4-시스템-아키텍처)
5. [데이터 모델 및 스키마](#5-데이터-모델-및-스키마)
6. [API 설계](#6-api-설계)
7. [프론트엔드 아키텍처](#7-프론트엔드-아키텍처)
8. [비즈니스 로직 및 핵심 기능](#8-비즈니스-로직-및-핵심-기능)
9. [폴더 구조, 공통 패턴](#9-폴더-구조-공통-패턴)
10. [보안 설계](#10-보안-설계)
11. [에러 처리 및 로깅](#11-에러-처리-및-로깅)
12. [성능 및 확장성](#12-성능-및-확장성)
13. [테스트 전략](#13-테스트-전략)
14. [배포 및 CI/CD](#14-배포-및-cicd)
15. [문서화 요구사항](#15-문서화-요구사항)
16. [마이그레이션 계획](#16-마이그레이션-계획)
17. [위험 요소 및 완화 전략](#17-위험-요소-및-완화-전략)
18. [참고 자료](#18-참고-자료)

## 1. 프로젝트 개요

### 1.1 프로젝트명
**Style License** - AI 기반 화풍 라이선싱 및 2차 창작 플랫폼

### 1.2 목적
디자인 작가가 자신의 스타일과 화풍을 거래할 수 있는 웹 플랫폼을 제공합니다. 화풍 거래를 라이선스 형식으로 진행하여 플랫폼에서 저작권을 인정하고, 사용자는 저작권이 보장된 상태로 작가의 화풍을 모방한 2차 창작물을 소유, 공유, 상업적으로 이용할 수 있습니다.

### 1.3 핵심 가치 제안
- 작가의 화풍에 대한 명확한 저작권 보호
- 합법적이고 투명한 AI 화풍 라이선싱
- 라이선스 기반의 2차 창작물 생성 및 상업적 이용 가능

### 1.4 주요 이해관계자
- **디자인 작가**: 화풍 라이선스 제공자, 수익 창출
- **일반 사용자**: 라이선스 구매자, 2차 창작물 생성자
- **플랫폼 운영자**: 라이선스 중개, 저작권 관리
---

## 2. 목표 및 비목표

### 2.1 Goals (목표)

#### 2.1.1 핵심 시스템 구축 (MVP)
- 작가의 화풍을 Fine-tuning한 AI 모델 생성 시스템 구축
- 토큰 기반 이미지 생성 과금 시스템 구현
- 사용자가 토큰을 소비하여 이미지 생성 및 다운로드
- 생성된 이미지에 작가 서명 자동 삽입 기능
- 기본적인 결제 및 토큰 충전 기능

#### 2.1.2 스타일(화풍) 생성 시스템
- 1인 1스타일 생성 가능 (MVP 단계)
- 작가가 자신의 화풍을 등록하여 Style(스타일 모델) 을 생성할 수 있는 시스템 구축
- **학습용 이미지**: 최소 10장 이상, 최대 100장까지 등록 가능
- 각각의 학습 이미지에 태그(학습 키워드) 입력 (⚠ 영어만 허용)
- **이미지 요구사항**:
  - 지원 형식: JPG, PNG
  - 최소 해상도: 512×512px
  - 최대 파일 크기: 10MB/장
- 스타일 생성 시 다음 정보를 반드시 입력: 
  - 스타일 제목 (Title)
  - 스타일 설명 (Description)
  - 이미지당 가격 (토큰 단가) — 1장 생성 시 소모되는 토큰 수
- 업로드된 이미지는 서버에서 검증(형식·크기 등) 후, RabbitMQ를 통해 학습 큐로 전달 → LoRA Fine-tuning 자동 실행
- 학습 완료 후 결과는 모델 파일(S3 저장) + Style 등록 완료 알림으로 작가에게 전달
- 학습된 모델 (스타일) 작가 임의로 삭제 불가능

#### 학습 진행 상황 추적
- 작가는 Edit / Create Style Page 에서 학습 진행 상황을 실시간으로 확인 가능
- 학습 상태 단계:
  - **pending**: 학습 대기 중
  - **training**: 학습 진행 중 (진행률 표시)
  - **completed**: 학습 완료
  - **failed**: 학습 실패
- 학습 진행 정보:
  - 현재 epoch / 전체 epoch
  - 진행률 퍼센트 (0-100%)
  - 예상 남은 시간 (초 단위)
  - 최근 업데이트 시간
- Training Server는 30초마다 Backend에 진행 상황 전송
- 프론트엔드는 5초마다 폴링하여 진행 상황 표시 (최대 30초 지연)

#### 2.1.3 이미지 생성 시스템 (Image Generation System)
- 사용자는 등록된 스타일(Style) 중 하나를 선택하여 이미지 생성 가능
- 이미지 생성 시 토큰이 자동 차감되며, 각 스타일별로 설정된 “이미지 1장당 소모 토큰 수” 기준을 따름
- 사용자는 프롬프트 입력란에 태그 기반 영어 키워드로 내용을 작성해야 하며, 이는 학습된 화풍의 맥락과 조합되어 최종 이미지를 생성
- 이미지 설명(Description) 을 함께 작성할 수 있으나 선택 사항
- 생성된 이미지는 **사용자의 마이페이지(My Page)**에 저장되며, 기본적으로 비공개 상태
- 지원 이미지 비율 : AI 생성 시스템은 아래의 세 가지 이미지 비율을 지원하며, 생성 요청 시 사용자가 선택 가능
  - **기본형 (Default)**: 1:1 비율, 512×512px, 일반 게시물용
  - **그리드형 (Grid / Large)**: 2:2 비율, 1024×1024px, 고해상도 출력용
  - **세로형 (Shorts / Story)**: 1:2 비율, 512×1024px, 세로 콘텐츠용
- 생성된 이미지에 작가 서명 자동 삽입, 제거 불가

#### 생성 진행 상황 추적
- 사용자는 마이페이지에서 이미지 생성 진행 상황을 확인 가능
- 생성 상태 단계:
  - **queued**: 생성 대기 중
  - **processing**: 생성 진행 중 (진행률 표시)
  - **completed**: 생성 완료
  - **failed**: 생성 실패
- 생성 진행 정보:
  - 현재 스텝 / 전체 스텝
  - 진행률 퍼센트 (0-100%)
  - 예상 남은 시간 (초 단위)
- Inference Server는 주요 단계마다 Backend에 진행 상황 전송
- 프론트엔드는 5초마다 폴링하여 진행 상황 표시

- **생성 실패 시**: 자동 재시도 최대 3회, 모두 실패 시 토큰 환불 + 알림 전송



#### 2.1.4 인증 시스템
- Google OAuth 소셜 로그인 (자체 로그인 없음)
- 일반 사용자 기본 권한
- 작가 권한 격상 신청 기능
- 작가 권한 격상 시 추가 정보 수집 (이메일, 서명 이미지)

#### 2.1.5 토큰 시스템 (최소 기능)
- 작가별 독립적인 토큰 가격 설정 기능 (이미지 1장당 소모 토큰)
- 사용자 토큰 구매 및 충전 기능 ( toss payment 해외 결제 모듈 활용 )
- 이미지 생성 시 토큰 자동 차감
- 토큰 거래 내역 조회

#### 2.1.6 저작권 보호 기능
- 생성 이미지에 작가 서명(워터마크) 자동 삽입
- 이미지 메타데이터에 작가 정보 기록

#### 2.1.7 태그 및 검색 시스템
- **학습 태깅 구조**
  - 작가가 모델 학습 시 각 이미지별로 태그를 수동 등록
  - **스타일 이름 자동 태그화**: 스타일 생성 시 스타일 이름이 모든 학습 이미지 태그에 자동으로 포함 하도록 등록
  - 학습 이미지(artworks)의 태그(artwork_tags)는 자동으로 집계되어 스타일(styles) 태그로 반영됨
- **검색 및 관리**
  - 태그 기반 스타일 검색 (스타일 이름 포함)
  - 작가 이름 검색
  - 태그별 활성화 여부(is_active), 검열 상태(is_flagged) 관리 가능
- **프롬프트 입력**
  - 이미지 생성 시 태그 기반 프롬프트 입력/조합 기능 제공
  - ⚠ 영어만 허용 (Stable Diffusion 프롬프트 호환성 고려)

#### 2.1.8 기본 커뮤니티 기능
- 생성된 이미지 공개/비공개 설정
- 이미지 설명 입력
- 공개 이미지 피드 조회
- 이미지 좋아요 기능
- 이미지 댓글 / 대댓글 기능
- 작가 팔로우/언팔로우 기능
- 내가 팔로우한 작가 목록 조회
- **MVP 제한사항**:
  - 이미지 물리 삭제 기능 제외 (비공개 전환으로 대체)
  - 작가의 팔로워 목록 조회 기능 제외

#### 2.1.9 알림 시스템
- 내 공개 이미지에 좋아요 알림
- 내 공개 이미지에 댓글 알림
- 작가의 모델 학습 완료 알림
- 내 이미지 생성 완료 알림
- 알림 목록 조회 및 읽음 처리

#### 2.1.10 다국어 지원
- 영어 기본 지원
- 한국어 지원
- UI 텍스트 다국어 처리 (i18n)


### 2.2 비목표 (MVP 이후 또는 제외)

#### 2.2.1 인증 고도화
- 자체 이메일/패스워드 로그인
- 추가 소셜 로그인 (카카오, 애플 등)
- 2단계 인증 (2FA)
- 작가 검증 시스템 (신원 확인, 포트폴리오 심사 등)

#### 2.2.2 스타일 검증 고도화
- 업로드된 학습 이미지의 저작권 자동 검증 (AI 이미지 식별, 중복 검사)
- 동일하거나 유사한 화풍 중복 탐지 (Style Similarity Check)
- 학습 데이터의 자동 품질 검수 (AI 기반 Blur/Low-res/NSFW 필터)
- 작가 신원 검증 (신분증, 포트폴리오 심사)

> **MVP에서는**: 작가가 업로드한 이미지를 신뢰하며, 기본적인 형식/크기 검증만 수행

#### 2.2.3 고급 기능
- 동영상 생성 기능
- 3D 모델 생성 기능
- NFT 발행 기능
- 실시간 협업 기능
- 이미지 편집 도구 (외부 도구 연동)
- AI 기반 자동 프롬프트 생성 및 최적화
- 작가 다중 스타일 생성 가능

#### 2.2.4 정산 및 수익화 고도화
- 작가의 토큰 현금 환전 기능
- 플랫폼의 토큰 수익 정산 시스템
- 세금 계산서 발행
- 주기적 정산 자동화
- 수익 분석 대시보드

#### 2.2.5 커뮤니티 고도화
- 무한 대댓글
- 작가 랭킹 시스템
- 큐레이션 및 추천 시스템
- 이미지 신고 및 관리 시스템
- 작가 프로필 커스터마이징
- **작가의 팔로워 목록 조회** (MVP 제외)
- **이미지 물리 삭제** (MVP 제외)

#### 2.2.6 알림 고도화
- 실시간 푸시 알림 (웹/모바일)
- 이메일 알림
- 알림 설정 커스터마이징 (알림 종류별 on/off)
- 알림 그룹화 및 요약

#### 2.2.7 검색 및 필터링 고도화
- 고급 검색 (복합 조건, 정렬 옵션)
- 카테고리 기반 분류
- AI 기반 유사 스타일 추천
- 텍스트 프롬프트 자동 태그 변환
- **인기 태그 API** (MVP 제외)
- **태그 자동완성 API** (MVP 제외)

#### 2.2.8 다국어 고도화
- 추가 언어 지원 (일본어, 중국어, 스페인어 등)
- 사용자 생성 콘텐츠(댓글, 설명) 자동 번역
- 지역별 콘텐츠 필터링

#### 2.2.9 기타
- 모바일 네이티브 앱 개발 (웹 우선)
- 이미지 일괄 생성 (배치 처리)
- 이미지 포트폴리오/갤러리 커스터마이징
- 오프라인 모드 지원
- API 공개 및 서드파티 연동

---

## 3. 배경 및 문제 정의

### 3.1 해결하고자 하는 문제
- AI 이미지 생성 시 원작가의 저작권 침해 문제
- 화풍 사용에 대한 불명확한 법적 권리
- 2차 창작물의 상업적 이용 제약
- 작가의 화풍이 무단으로 학습되어 수익 창출 기회 상실

### 3.2 기존 솔루션의 한계
- **Midjourney/DALL-E**: 작가 화풍 학습에 대한 보상 없음, 저작권 불명확
- **Stable Diffusion (오픈소스)**: 무단 학습 가능, 작가 수익화 메커니즘 부재
- **직접 커미션**: 높은 비용, 긴 제작 시간, 확장성 부족

### 3.3 우리 솔루션의 차별점
- 향후 AI 저작권 제도 변화에 선제적으로 대응
- 작가가 직접 화풍을 등록하고 라이선스 판매
- 생성 이미지마다 작가 서명 자동 삽입으로 저작권 명시
- 토큰 기반 수익 분배로 작가 수익 보장
- 합법적 2차 창작물 상업적 이용 가능

---

## 4. 시스템 아키텍처

### 4.1 전체 시스템 구조도 (GCP 기반 MVP)
```
                           ┌─────────────────┐
┌──────────┐  HTTPS (CDN)  │ Cloud Storage   │
│          ├───────────────┤(Frontend/이미지) │
│   User   │               └─────────────────┘
│          │  HTTPS (API)
└──────────┘      │
                  ↓
            ┌───────────┐
            │ Cloud Run │
            │ (Backend) │
            └───────────┘
    ┌───────────┴───────────┐
    │                         │
    ↓                         ↓
┌───────────┐           ┌───────────┐
│ Cloud SQL │           │ RabbitMQ  │
│(PostgreSQL)│          (on GCE VM) │
└───────────┘           └───────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ↓                         ↓
         ┌───────────────┐       ┌───────────────┐
         │Training Server│       │Inference Server│
         │  (GCE + GPU)  │       │  (GCE + GPU)  │
         └───────────────┘       └───────────────┘
```

### 4.2 컴포넌트 설명

#### Frontend (Vue 3)
- 사용자 인터페이스 제공
- Google OAuth 로그인 처리
- 이미지 업로드/다운로드
- 실시간 생성 상태 폴링
- **(운영 환경)** **Google Cloud Storage**에 정적 파일로 배포, **Cloud CDN**을 통해 전 세계에 캐시하여 제공.

#### Backend (Django)
- REST API 서버
- 세션 기반 인증/인가
- 비즈니스 로직 처리
- RabbitMQ 작업 전송
- 토큰 트랜잭션 관리
- **(운영 환경)** 컨테이너화하여 **Google Cloud Run**에 배포. 트래픽에 따라 자동 확장/축소.

#### PostgreSQL
- 사용자, 모델, 이미지 메타데이터 저장
- 토큰 트랜잭션 기록
- ACID 트랜잭션 보장
- **(운영 환경)** **Google Cloud SQL for PostgreSQL** 사용. 완전 관리형 서비스로 백업, 복제, 보안 자동 관리.

#### RabbitMQ
- 비동기 작업 큐
- `model_training` 큐: 모델 학습 작업
- `image_generation` 큐: 이미지 생성 작업
- **(운영 환경)** **Google Compute Engine(GCE)**의 저렴한 VM(e.g., e2-small)에서 Docker 컨테이너로 실행.

#### Training Server
- **(운영 환경)** **Google Compute Engine(GCE) VM + GPU** (예: **NVIDIA L4**) 사용.
  - **Spot VM(선점형)** 옵션을 활용하여 학습 비용을 60~90% 절감.
- Stable Diffusion 기반 LoRA Fine-tuning
- 학습 진행 상황 30초마다 Backend API로 전송
- 학습 완료 시 Backend Webhook 호출
- 모델 파일을 **Cloud Storage**에 저장.

#### Inference Server
- **(운영 환경)** **Google Compute Engine(GCE) VM + GPU** (예: **NVIDIA T4**) 사용.
  - 24/7 운영을 위해 **약정 사용 할인(CUD)** 적용 고려.
- LoRA 가중치 로드 후 이미지 생성
- 생성 진행 상황 실시간 Backend API로 전송
- 서명 자동 삽입 (PIL)
- 생성 이미지를 **Cloud Storage**에 저장.
- 생성 완료 시 Backend Webhook 호출

#### Cloud Storage
- **(구 S3)**
- **프론트엔드 파일** 호스팅
- **학습/생성 이미지** 저장
- **학습 완료 모델 파일** 저장

### 4.3 데이터 흐름

#### 모델 학습 플로우
```
작가 → Frontend: 이미지 업로드
Frontend → Backend(Cloud Run): POST /api/styles
Backend → Cloud Storage: 이미지 저장
Backend → RabbitMQ: 학습 작업 전송
RabbitMQ → Training Server(GCE): 작업 수신
Training Server: LoRA Fine-tuning
Training Server → Cloud Storage: 모델 파일 저장
Training Server → Backend(Cloud Run): POST /api/webhooks/training/complete
Backend → Frontend: 알림 (학습 완료)
```

#### 이미지 생성 플로우
```
사용자 → Frontend: 프롬프트 입력
Frontend → Backend(Cloud Run): POST /api/generations
Backend: 토큰 차감 (SELECT FOR UPDATE)
Backend → RabbitMQ: 생성 작업 전송
RabbitMQ → Inference Server(GCE): 작업 수신
Inference Server: 이미지 생성 + 서명 삽입
Inference Server → Cloud Storage: 이미지 저장
Inference Server → Backend(Cloud Run): POST /api/webhooks/inference/complete
Backend → Frontend: 이미지 URL 반환
```

### 4.4 기술 스택 선정 이유
| 기술 | 선정 이유 |
|------|-----------|
| **Vue 3** | 낮은 러닝 커브, Composition API의 유연성, 한국어 커뮤니티 활성화 |
| **JavaScript** | TypeScript 대비 빠른 프로토타이핑, Zod로 런타임 검증 보완 |
| **Django** | Python AI/ML 생태계와 통합 용이, Admin 패널 기본 제공 |
| **PostgreSQL** | ACID 보장, 복잡한 관계형 쿼리 지원, JSON 필드 지원 |
| **RabbitMQ** | 장시간 AI 작업의 안정적 비동기 처리, 재시도 메커니즘 |
| **Stable Diffusion** | 오픈소스, LoRA Fine-tuning 지원, 커뮤니티 활성화 |
| **Docker** | 개발/운영 환경 일관성, GPU 서버 격리 |

> **상세 내용**: 각 컴포넌트별 아키텍처는 다음 문서 참조
> - Backend: [apps/backend/README.md](apps/backend/README.md)
> - Frontend: [apps/frontend/README.md](apps/frontend/README.md)
> - Training Server: [apps/training-server/README.md](apps/training-server/README.md)
> - Inference Server: [apps/inference-server/README.md](apps/inference-server/README.md)

---

## 5. 데이터 모델 및 스키마

### 5.1 개요

PostgreSQL 15.x 기반, 7개 논리적 스키마로 구성

### 5.2 스키마 구조
```
style_license_db
├── auth           # 사용자 인증 (users, artists)
├── token          # 토큰 거래 및 결제 (transactions, purchases)
├── style          # 화풍 모델 (styles, artworks)
├── generation     # 이미지 생성 (generations)
├── community      # 소셜 기능 (follows, likes, comments)
├── tagging        # 태그 시스템 (tags, M:N 테이블들)
└── system         # 알림 (notifications)
```

### 5.3 핵심 엔티티

| 엔티티 | 설명 | 주요 필드 |
|--------|------|-----------|
| **users** | 사용자 계정 | token_balance, role(user/artist) |
| **artists** | 작가 프로필 (1:1) | earned_token_balance, follower_count, signature_image_url |
| **transactions** | 토큰 거래 내역 | sender, receiver, amount, status, transaction_type |
| **purchases** | 토스 결제 기록 | amount_tokens, status, provider_payment_key |
| **styles** | 화풍 모델 | training_status, generation_cost_tokens |
| **artworks** | 학습 이미지 (10~100장) | image_url, is_valid |
| **generations** | 생성 요청/결과 | status, result_url, is_public |
| **tags** | 태그 마스터 (영어) | name, usage_count |

### 5.4 핵심 관계
```
users ─┬─ artists (1:1)
       ├─ styles ── artworks (1:N)
       ├─ generations
       ├─ follows (N:N self)
       └─ likes, comments

styles ── generations (1:N, ON DELETE RESTRICT)
tags ──── styles/artworks/generations (M:N)
```

### 5.5 주요 제약 조건

- 토큰 잔액 음수 불가: `token_balance >= 0`
- 중복 팔로우/좋아요 방지: UNIQUE 제약
- 사용 중인 스타일 삭제 불가: ON DELETE RESTRICT
- 자기 팔로우 방지: `follower_id != following_id`

### 5.6 성능 전략

- **캐싱 컬럼**: follower_count (artists), like_count, comment_count (generations)
- **인덱스**: 모든 FK + (user_id, created_at) 복합 인덱스
- **동시성**: 토큰 차감 시 `SELECT FOR UPDATE`
- **소프트 삭제**: is_active, is_flagged 플래그

> **상세 정보**: [docs/database/README.md](../docs/database/README.md) 참조

---

## 6. API 설계

### 6.1 API 개요

#### 6.1.1 설계 원칙
- **RESTful 아키텍처**: 리소스 기반 URL 설계, HTTP 메서드 활용
- **Session-based Authentication**: Django 세션 쿠키 기반 인증
- **JSON 통신**: 모든 요청/응답은 `application/json`
- **HTTPS 필수**: 프로덕션 환경
- **멱등성 보장**: 동일 요청 반복 시 동일 결과 (결제, 중복 방지 등)

#### 6.1.2 Base URL
- **개발**: `http://localhost:8000`
- **프로덕션**: `https://api.stylelicense.com`

**엔드포인트**: 모든 API는 `/api/...` 형식으로 시작 (버전 번호 미포함)
**전체 URL**: Base URL + 엔드포인트 (예: `http://localhost:8000/api/auth/me`)

#### 6.1.3 공통 응답 형식

**성공**:
```json
{
  "success": true,
  "data": { "id": 123, "field": "value" }
}
```

**에러**:
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_TOKENS",
    "message": "토큰 잔액이 부족합니다",
    "details": { "required": 100, "available": 50 }
  }
}
```

**페이지네이션** (Cursor-based):
```json
{
  "success": true,
  "data": {
    "results": [...],
    "next_cursor": "2025-01-15T12:34:56Z",
    "has_more": true
  }
}
```

---

### 6.2 API 그룹 개요

프로젝트는 다음 7개의 API 그룹으로 구성됩니다:

| 그룹 | 엔드포인트 예시 | 주요 기능 |
|------|---------------|-----------|
| **인증** | `/api/auth/*` | Google OAuth, 로그인/로그아웃 |
| **사용자** | `/api/users/*` | 프로필 조회/수정, 작가 권한 신청 |
| **토큰** | `/api/tokens/*` | 잔액 조회, 구매, 거래 내역 |
| **화풍** | `/api/styles/*` | 스타일 생성/조회/수정, 학습 진행 |
| **생성** | `/api/generations/*` | 이미지 생성 요청/조회, 공개 피드 |
| **커뮤니티** | `/api/users/:id/follow`, `/api/generations/:id/like` | 팔로우, 좋아요, 댓글 |
| **검색/알림** | `/api/search`, `/api/notifications` | 통합 검색, 알림 목록 |

**상세 명세**: [docs/API.md](docs/API.md)

---

### 6.2.1 사용자 시스템

#### 핵심 엔드포인트
- `GET /api/users/:id` - 사용자 프로필 조회 (공개)
- `PATCH /api/users/me` - 내 프로필 수정 (인증 필요)
- `POST /api/users/me/upgrade-to-artist` - 작가 권한 신청 (인증 필요)

#### 주요 기능
- **프로필 조회**: 다른 사용자의 공개 프로필 확인 (통계 포함)
- **프로필 수정**: username, bio, profile_image 업데이트
- **작가 승격**: 일반 사용자가 작가로 전환 (artist_name, verified_email, signature_image 제출)

**상세 명세**: [docs/API.md#3-사용자-api](docs/API.md#3-사용자-api)

---

### 6.3 인증 시스템

#### 6.3.1 인증 플로우
```
1. GET /api/auth/google/login → Google OAuth 시작
2. Google 동의 → Callback /api/auth/google/callback
3. Backend → 세션 쿠키 설정 + 프론트엔드 리다이렉트
4. 이후 모든 요청 → 세션 쿠키 자동 포함
```

#### 6.3.2 핵심 엔드포인트
- `GET /api/auth/google/login` - OAuth 시작
- `GET /api/auth/google/callback` - OAuth 콜백
- `GET /api/auth/me` - 현재 사용자 정보
- `POST /api/auth/logout` - 로그아웃

#### 6.3.3 권한 관리
- **일반 사용자** (`role='user'`): 이미지 생성, 토큰 구매
- **작가** (`role='artist'`): 일반 권한 + 스타일 생성
- 작가 신청: `POST /api/users/me/upgrade-to-artist`

**상세 명세**: [docs/API.md#auth-api](docs/API.md#auth-api)

---

### 6.4 토큰 시스템

#### 6.4.1 토큰 이코노미
```
[충전] 사용자 → 토스 결제 → 플랫폼 → 토큰 발급
[사용] 이미지 생성 시 사용자 토큰 차감 → 작가 수익 증가
[정산] 작가 토큰 → 현금 환전 (MVP 제외, 향후 구현)
```

#### 6.4.2 핵심 엔드포인트
- `GET /api/tokens/balance` - 토큰 잔액 조회
- `POST /api/tokens/purchase` - 토큰 구매 시작 (토스 결제)
- `GET /api/tokens/transactions` - 거래 내역 (충전/사용 통합)

**거래 내역 필터**:
```
GET /api/tokens/transactions?type=purchase  # 충전만
GET /api/tokens/transactions?type=generation  # 사용만
GET /api/tokens/transactions?type=all       # 전체 (기본값)
```

#### 6.4.3 결제 플로우
```
1. POST /api/tokens/purchase
2. Backend → purchases 레코드 생성 (status='pending')
3. Backend → 결제 URL 반환
4. 토스 결제 완료 → Webhook /api/webhooks/toss/payment
5. Backend → token_balance 증가 + status='paid'
```

#### 6.4.4 주요 특징
- 사용자 간 토큰 전송 불가
- 작가는 자신의 스타일 사용 시에도 토큰 차감 (공정성)
- 모든 토큰 거래는 `transactions` 테이블에 기록

**상세 명세**: [docs/API.md#token-api](docs/API.md#token-api)

---

### 6.5 화풍(Style) 시스템

#### 6.5.1 핵심 엔드포인트
- `GET /api/styles` - 스타일 목록 (필터, 정렬, 페이지네이션)
- `GET /api/styles/:id` - 스타일 상세 + 학습 진행 상황
- `POST /api/styles` - 스타일 생성 (학습 요청)
- `PATCH /api/styles/:id` - 메타데이터 수정
- `GET /api/styles/me` - 내 스타일 목록

#### 6.5.2 스타일 생성 규칙
- **이미지**: 10~100장 (JPG, PNG, 최소 512×512px, 최대 10MB/장)
- **태그**: 영어만 허용
- **MVP 제한**: 작가당 1개 스타일만 생성 가능
- **학습 시간**: 30분~2시간 (이미지 수에 따라)

#### 6.5.3 학습 상태
- `pending` - 업로드 완료, 검증 대기
- `training` - 학습 진행 중 (진행률 표시)
- `completed` - 학습 완료, 사용 가능
- `failed` - 학습 실패

#### 6.5.4 진행 상황 조회 (중요 변경사항)
**별도 `/progress` 엔드포인트 제거**, 메인 리소스에서 통합 조회:

```json
GET /api/styles/:id
{
  "id": 10,
  "name": "My Style",
  "training_status": "training",
  "progress": {
    "current_epoch": 50,
    "total_epochs": 100,
    "progress_percent": 50,
    "estimated_seconds": 900,
    "last_updated": "2025-01-15T12:00:00Z"
  }
}
```

- `training_status='training'`일 때만 `progress` 객체 존재
- 완료/실패 시 `progress=null`
- Training Server는 30초마다 Backend에 진행 상황 전송
- 프론트엔드는 동적 폴링 (queued: 30초, training: 5초)

#### 6.5.5 스타일 정렬 옵션 (명확화)
```
GET /api/styles?sort=recent   # created_at DESC (기본값)
GET /api/styles?sort=popular  # 팔로워 많은 작가 우선 → created_at DESC
```

**popular 정렬 기준**:
1. 1차: 작가 팔로워 수 (`artist.follower_count DESC`)
2. 2차: 최신순 (`created_at DESC`)

**상세 명세**: [docs/API.md#styles-api](docs/API.md#styles-api)

---

### 6.6 이미지 생성 시스템

#### 6.6.1 핵심 엔드포인트
- `POST /api/generations` - 이미지 생성 요청
- `GET /api/generations/:id` - 생성 상태 + 결과 조회
- `GET /api/generations/feed` - 공개 피드
- `GET /api/generations/me` - 내 생성 이미지 목록
- `PATCH /api/generations/:id` - 공개 여부, 설명 수정

**MVP 제한**: 이미지 삭제 불가, 비공개 전환(`is_public=false`)으로 대체

#### 6.6.2 생성 요청 파라미터
```json
POST /api/generations
{
  "style_id": 10,
  "prompt_tags": ["woman", "portrait", "sunset"],
  "description": "노을 배경의 여성 초상화",
  "aspect_ratio": "1:1",  // 1:1, 2:2, 1:2
  "seed": 42
}
```

#### 6.6.3 생성 플로우
```
1. 토큰 차감 (원자적 트랜잭션)
2. RabbitMQ 큐 전송 (status='queued')
3. Inference Server 처리 (status='processing')
4. 이미지 생성 + 서명 삽입
5. S3 업로드 (status='completed')
6. 알림 전송
```

#### 6.6.4 진행 상황 조회 (중요 변경사항)
**별도 `/progress` 엔드포인트 제거**, 메인 리소스에서 통합 조회:

```json
GET /api/generations/:id
{
  "id": 500,
  "status": "processing",
  "progress": {
    "current_step": 38,
    "total_steps": 50,
    "progress_percent": 76,
    "estimated_seconds": 3,
    "last_updated": "2025-01-15T12:00:05Z"
  }
}
```

- `status='processing'`일 때만 `progress` 객체 존재
- 완료/실패 시 `progress=null`

#### 6.6.5 실패 처리 (상세화)
**재시도 전략**:
1. **재시도 대상 오류**:
   - GPU OOM, 타임아웃, 네트워크 오류 → 자동 재시도
   - 잘못된 프롬프트, 모델 없음 → 즉시 실패

2. **재시도 로직**:
   - 최대 3회, 지수 백오프 (0초, 30초, 120초)
   - `status='retrying'` 표시
   - 토큰은 최초 1회만 차감, 재시도 비용은 플랫폼 부담

3. **최종 실패 시**:
   - 토큰 전액 환불
   - `status='failed'` + 에러 알림

**상세 명세**: [docs/API.md#generations-api](docs/API.md#generations-api)

---

### 6.7 커뮤니티 기능

#### 6.7.1 소셜 기능 엔드포인트

| 기능 | 엔드포인트 | 메서드 |
|------|-----------|--------|
| 팔로우 | `/api/users/:id/follow` | POST |
| 언팔로우 | `/api/users/:id/follow` | DELETE |
| 팔로잉 목록 | `/api/users/me/following` | GET |
| 좋아요 | `/api/generations/:id/like` | POST |
| 좋아요 취소 | `/api/generations/:id/like` | DELETE |
| 댓글 목록 | `/api/generations/:id/comments` | GET |
| 댓글 작성 | `/api/generations/:id/comments` | POST |
| 댓글 수정 | `/api/comments/:id` | PATCH |
| 댓글 삭제 | `/api/comments/:id` | DELETE |

#### 6.7.2 MVP 제한사항
- **팔로워 목록 조회 불가**: 내가 팔로잉하는 목록만 조회 가능
- **1단계 대댓글만**: 대댓글의 대댓글 불가 (`parent_id` 1단계만)
- **댓글 좋아요 없음**: 생성물 좋아요만 지원

**상세 명세**: [docs/API.md#community-api](docs/API.md#community-api)

---

### 6.8 검색 시스템 (단순화)

#### 6.8.1 통합 검색 엔드포인트
```
GET /api/search?q=watercolor&type=all
```

**type 파라미터**:
- `all` (기본값) - 스타일 + 작가 통합 검색
- `styles` - 스타일만 (태그 + 스타일 이름)
- `artists` - 작가만 (작가명 + 유저명)

#### 6.8.2 응답 구조
```json
{
  "success": true,
  "data": {
    "styles": [
      {
        "id": 10,
        "name": "Watercolor Dreams",
        "thumbnail_url": "...",
        "artist": { "id": 5, "artist_name": "John" },
        "matched_by": "tag"  // "tag" | "name"
      }
    ],
    "artists": [
      {
        "id": 5,
        "username": "watercolor_master",
        "artist_name": "Watercolor Master",
        "follower_count": 1234,
        "matched_by": "name"
      }
    ]
  }
}
```

#### 6.8.3 검색 로직
- **스타일**: 태그 검색 + 스타일 이름 검색 (자동 태그 포함)
- **작가**: `artists.artist_name` + `users.username` 검색
- **MVP 제외**: 인기 태그 API, 자동완성 API

**상세 명세**: [docs/API.md#search-api](docs/API.md#search-api)

---

### 6.9 알림 시스템

#### 6.9.1 알림 타입
- `follow` - 팔로우 알림
- `like` - 좋아요 알림
- `comment` - 댓글 알림
- `generation_complete` - 생성 완료 (시스템)
- `generation_failed` - 생성 실패 (시스템)
- `style_training_complete` - 학습 완료 (시스템)
- `style_training_failed` - 학습 실패 (시스템)

#### 6.9.2 핵심 엔드포인트
- `GET /api/notifications` - 알림 목록 (페이지네이션)
- `PATCH /api/notifications/:id/read` - 읽음 처리
- `POST /api/notifications/read-all` - 모든 알림 읽음

**상세 명세**: [docs/API.md#notifications-api](docs/API.md#notifications-api)

---

### 6.10 Webhook API (내부 전용)

#### 6.10.1 인증 방식 (강화)
```http
Authorization: Bearer <INTERNAL_API_TOKEN>
X-Request-Source: training-server | inference-server
```

**보안 설정**:
- 환경변수로 관리: `INTERNAL_API_TOKEN` (긴 UUID)
- IP 화이트리스트: AI 서버 IP만 허용
- 토큰 Rotation: 월 1회

#### 6.10.2 주요 Webhook

**결제 완료** (토스):
```
POST /api/webhooks/toss/payment
```

**스타일 학습 완료/실패**:
```
POST /api/webhooks/training/complete
POST /api/webhooks/training/failed
```

**이미지 생성 완료/실패**:
```
POST /api/webhooks/inference/complete
POST /api/webhooks/inference/failed
```

**진행 상황 업데이트**:
- Training Server → `PATCH /api/webhooks/training/progress` (progress JSONB 업데이트)
- Inference Server → `PATCH /api/webhooks/inference/progress` (progress JSONB 업데이트)

**상세 명세**: [docs/API.md#webhooks](docs/API.md#webhooks)

---

### 6.11 Rate Limiting (재설계)

#### 6.11.1 제한 정책

| 엔드포인트 유형 | 제한 | 식별 기준 |
|--------------|------|----------|
| 로그인 시도 | 5회 / 5분 | IP |
| 이미지 생성 | 6회 / 분 | User ID (GPU 처리 속도 고려) |
| 기타 인증 API | 100회 / 분 | User ID |
| 비인증 API | 50회 / 분 | IP |

#### 6.11.2 초과 시 처리
- HTTP 429 반환
- `Retry-After` 헤더 포함 (초 단위)

#### 6.11.3 구현 방식
- 라이브러리: `django-ratelimit`
- 슬라이딩 윈도우 방식

**상세 명세**: [docs/API.md#rate-limiting](docs/API.md#rate-limiting)

---

### 6.12 에러 코드 체계

#### 6.12.1 HTTP 상태 코드

| 코드 | 의미 | 주요 사용 |
|------|------|----------|
| 200 | OK | 성공 |
| 201 | Created | 리소스 생성 성공 |
| 400 | Bad Request | 잘못된 요청 |
| 401 | Unauthorized | 인증 필요 |
| 402 | Payment Required | 토큰 부족 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 409 | Conflict | 리소스 충돌 |
| 422 | Unprocessable | 검증 실패 |
| 429 | Too Many Requests | Rate Limit 초과 |
| 500 | Server Error | 서버 오류 |

#### 6.12.2 주요 애플리케이션 에러 코드

**인증/권한**:
- `UNAUTHORIZED` (401)
- `FORBIDDEN` (403)
- `ARTIST_ONLY` (403)

**토큰**:
- `INSUFFICIENT_TOKENS` (402)
- `PAYMENT_FAILED` (402)

**스타일**:
- `STYLE_LIMIT_REACHED` (403) - MVP: 1개 제한
- `STYLE_NOT_READY` (422) - 학습 미완료
- `TRAINING_FAILED` (500)

**이미지**:
- `INVALID_IMAGE_FORMAT` (422)
- `IMAGE_SIZE_EXCEEDED` (422)
- `GENERATION_FAILED` (500)

**커뮤니티**:
- `DUPLICATE_FOLLOW` (409)
- `SELF_FOLLOW_NOT_ALLOWED` (400)
- `REPLY_DEPTH_EXCEEDED` (422)

**전체 목록**: [docs/API.md#error-codes](docs/API.md#error-codes)

---

### 6.13 보안 고려사항

#### 6.13.1 CSRF 보호
- 모든 변경 요청 (`POST`, `PUT`, `PATCH`, `DELETE`)에 CSRF 토큰 필수
- Django 기본 미들웨어 사용

#### 6.13.2 세션 보안
- `httponly` 쿠키: XSS 방어
- `secure` 쿠키: HTTPS 전송만 (프로덕션)
- `samesite=lax`: CSRF 추가 방어

#### 6.13.3 입력 검증
- 모든 입력값 서버 재검증 (DRF Serializer)
- SQL Injection, XSS 방어

---

### 6.14 참조 문서

완전한 API 명세 및 관련 문서:
- **전체 API 명세**: [docs/API.md](docs/API.md) ← 구현 시 필수 참조
- **데이터베이스 스키마**: [docs/database/README.md](docs/database/README.md)
- **쿼리 예제**: [docs/database/guides/QUERIES.md](docs/database/guides/QUERIES.md)
- **보안 정책**: [docs/SECURITY.md](docs/SECURITY.md)

---

## 7. 프론트엔드 아키텍처

### 7.1 기술 스택
- **프레임워크**: Vue 3 (Composition API, JavaScript 기반)
- **상태 관리**: Pinia
- **라우팅**: Vue Router
- **스타일링**: Tailwind CSS
- **다국어 처리**: Vue I18n
- **빌드 도구**: Vite

> ※ TypeScript는 사용하지 않으며, 런타임 검증(Zod 등)과 ESLint를 통해 코드 안정성을 확보합니다.

---

### 7.2 주요 페이지 구성
- **Main Page**: 플랫폼 메인 / 공개 피드 그리드
- **Feed Detail Page**: 개별 피드(이미지)의 상세보기
  - **Comment Modal**: 댓글 목록보기
- **Search & Following Artist Page**: 스타일 검색 및 팔로우 목록 조회
  - **상단**: 검색창 (태그 기반 스타일 검색, 작가 이름 검색)
  - **정렬 옵션**: 최신순(recent), 인기순(popular - 팔로워 많은 작가 우선)
  - **팔로잉 섹션**: 내가 팔로잉한 작가들의 스타일 목록 (고정 영역)
    - 팔로잉한 작가가 없으면 빈 상태 표시
  - **전체 스타일 그리드**: 검색 결과 또는 전체 스타일 목록
- **Style Detail Page**: 특정 스타일(작가)의 상세 정보 및 이미지 생성 화면
- **My Page**: 정보 수정, 스타일 관리 페이지, 결제 페이지 이동 버튼 / 공개, 비공개 피드 그리드 
- **Edit / Create Style Page**: 새로운 화풍(모델) 생성 / 업로드 / 가격, 설명 수정
- **Edit Profile**: 사용자 프로필 및 정보 수정
- **Payment Page**: 토큰 결제 내역, 토큰 사용 내역 조회, 토큰 구매
- **Notification Page**: 알림 내역 조회 및 읽음 처리

---

### 7.3 상태 관리 전략
- 각 주요 도메인(`auth`, `models`, `generation`, `community`)별로 **독립적인 Pinia 스토어** 운영
- 공통 로직(페이지네이션, API 에러 처리 등)은 **Composable 훅**으로 공유
- 전역 상태는 최소화하며, 세션/테마 수준만 전역으로 유지

---

### 7.4 라우팅 전략
- **인증 필요 라우트**: 로그인 여부에 따라 접근 제한 (`meta.requiresAuth`)
- **작가 전용 라우트**: 사용자 권한(Role) 검증 후 접근 허용
- **지연 로딩(Lazy Loading)**을 통해 페이지 단위 번들 크기 최소화
- **가드(Guards)**를 통해 로그인/권한/CSRF 상태를 일관되게 점검
- **다국어 URL Prefix**(`/ko`, `/en`) 적용을 고려한 라우팅 구조 유지

> **상세 구조**: [apps/frontend/README.md](apps/frontend/README.md)

---

## 8. 비즈니스 로직 및 핵심 기능

### 8.1 화풍 모델 학습 (Fine-tuning)

#### 처리 플로우
1. 작가가 10장 이상의 학습 이미지 업로드
2. Backend에서 이미지 검증 (형식, 크기, 저작권 확인)
3. RabbitMQ 큐에 학습 작업 전송
4. GPU Server가 작업 수신
5. Stable Diffusion 기반 LoRA Fine-tuning 실행
6. 학습된 모델을 스토리지에 저장
7. DB에 모델 상태 업데이트 (completed/failed)
8. 작가에게 알림 전송

#### 비즈니스 규칙
- 최소 10장, 최대 100장의 학습 이미지 필요
- 이미지 해상도: 512x512 이상
- 지원 형식: JPG, PNG
- 학습 시간: 약 30분 ~ 2시간 (이미지 수에 따라)
- **스타일 이름 자동 태그화**: 스타일 생성 시 스타일 이름(title)이 자동으로 모든 학습 이미지에 소문자 태그로 등록됨
  - 예: "Watercolor Dreams" → "watercolor dreams" 태그 자동 생성

### 8.2 이미지 생성 및 서명 삽입

#### 처리 플로우
1. 사용자가 프롬프트 태그 형식, 이미지 내용 입력 및 스타일 (모델) 선택
2. Backend에서 토큰 잔액 확인
3. 토큰 차감 (미리 차감 또는 생성 성공 후 차감)
4. RabbitMQ 큐에 이미지 생성 작업 전송
5. GPU Server가 이미지 생성
6. **생성된 이미지에 작가 서명 자동 삽입**
7. 서명 포함 이미지를 스토리지에 저장
8. DB에 생성 이력 기록
9. 사용자에게 이미지 반환

#### 비즈니스 규칙
- 토큰 부족 시 이미지 생성 불가
- 이미지 생성 실패 시 토큰 환불
- 서명은 위치/크기/투명도 규칙 고정, 제거 불가 (원본 이미지는 사용자 접근 불가)
- 생성된 이미지는 자동으로 작가 정보 메타데이터 포함

### 8.3 토큰 시스템

#### 토큰 가격 책정
- 작가가 모델 등록 시 1장당 토큰 가격 설정 (1 ~ 10000 범위)
- 플랫폼 수수료: 없음 (MVP에서는 작가가 100% 수취)

#### 웰컴 토큰 (신규 가입 보너스)
- **지급 시점**: Google OAuth 최초 가입 시 자동 지급
- **지급 수량**: 100 토큰
- **거래 기록**: `transactions` 테이블에 기록
  - `sender_id`: NULL (플랫폼에서 지급)
  - `receiver_id`: 신규 사용자 ID
  - `amount`: 100
  - `status`: 'completed'
  - `memo`: 'Welcome Bonus'
  - `related_generation_id`: NULL
- **목적**: 신규 사용자가 토큰 구매 없이 플랫폼 체험 가능

#### 토큰 구매
- **결제 수단**: 신용카드, 간편결제 (토스페이먼츠) (해외 결제 고려)
- **토큰 패키지** (서버에서 정의, 클라이언트 조작 불가):
  - `basic_100`: 100 토큰, ₩10,000 (₩100/토큰)
  - `standard_500`: 500 토큰, ₩45,000 (₩90/토큰, 10% 할인)
  - `premium_1000`: 1000 토큰, ₩80,000 (₩80/토큰, 20% 할인)
- **보안**: 가격은 서버 측 패키지 정의에서만 조회, 클라이언트는 package_id만 전달

#### 토큰 소비
- 이미지 생성 요청 시 즉시 차감
- 생성 실패 시 자동 환불
- 동시성 제어: PostgreSQL SELECT FOR UPDATE

#### 토큰 정산 (MVP 제외)
- 작가의 토큰 → 현금 환전 기능은 MVP 이후 구현

### 8.4 알림 시스템

#### 알림 트리거
- 내 이미지에 좋아요: `image_liked`
- 내 이미지에 댓글: `image_commented`
- 모델 학습 완료: `model_training_completed`
- 모델 학습 실패: `model_training_failed`
- 이미지 생성 완료: `image_generation_completed`
- 이미지 생성 실패: `image_generation_failed`

#### 진행 상황 확인 
- 학습/생성 진행 중: 마이페이지에서 실시간 진행률 확인 가능 (폴링 방식)
- 완료/실패 시: 알림 전송

#### 알림 전달
- MVP: 웹 내 알림 목록 조회
- 향후: WebSocket 실시간 알림, 이메일 알림

### 8.5 태그 시스템

#### 태그 등록
- **자동 등록**: 스타일 생성 시 스타일 이름이 학습 이미지마다 자동으로 태그로 등록됨
  - 예: 스타일 이름 "Watercolor Dreams" → 태그 "watercolor dreams" 생성
- **수동 등록**: 모델 학습 시 작가가 추가 태그 입력 (예: "portrait", "anime")
- 개별 학습 이미지마다 태그 설정 가능
- 모든 태그는 소문자로 정규화되어 저장

#### 태그 기반 검색
- 통합 검색 API: 태그 기반 스타일 검색 + 작가 이름 검색
- 스타일 이름 자체가 태그이므로 별도의 스타일 이름 검색 불필요

#### 태그 기반 프롬프트
- 사용자가 이미지 생성 시 태그 입력 (예: "watercolor woman portrait")
- ⚠ 영어만 허용 (Stable Diffusion 프롬프트 호환성)

---

## 9. 폴더 구조, 공통 패턴

### 9.1 Monorepo 구조
```
project-root/
├── apps/
│   ├── backend/          # 개발용 Django API 서버
│   ├── frontend/         # 개발용 Vue 3 SPA
│   ├── training-server/  # LoRA 학습 서버
│   └── inference-server/ # 이미지 생성 서버
├── docs/                 # 공통 문서
└── design/               # 디자인 리소스
```

**개발 vs 배포**:
- `apps/backend/`, `apps/frontend/`: 개발용 코드 (이곳에서 개발)
- **로컬 개발**: 루트의 `docker-compose.yml` 사용 (전체 스택 로컬 실행)
- **프로덕션 배포**: GCP 서비스별 개별 배포 (Cloud Run, Cloud Storage, GCE 등)

### 9.2 공통 패턴
- API 응답 형식: [docs/PATTERNS.md](docs/PATTERNS.md)
- RabbitMQ 메시지 포맷: [docs/PATTERNS.md](docs/PATTERNS.md)
- 에러 코드 규칙: [docs/PATTERNS.md](docs/PATTERNS.md)

> **상세 코드 가이드**:
> - Backend: [apps/backend/CODE_GUIDE.md](apps/backend/CODE_GUIDE.md)
> - Frontend: [apps/frontend/CODE_GUIDE.md](apps/frontend/CODE_GUIDE.md)
> - Training: [apps/training-server/CODE_GUIDE.md](apps/training-server/CODE_GUIDE.md)
> - Inference: [apps/inference-server/CODE_GUIDE.md](apps/inference-server/CODE_GUIDE.md)


---

## 10. 보안 설계

### 10.1 인증 및 인가

#### Google OAuth 2.0
- **라이브러리**: Django-allauth
- **플로우**: Authorization Code Flow
- **세션 관리**: Django Session (httponly cookie)
- **세션 만료**: 2주 (재로그인 필요)

#### 권한 관리
- **일반 사용자**: 이미지 생성, 토큰 구매, 댓글, 좋아요
- **작가**: 일반 사용자 권한 + 모델 생성

#### API 보호
- 모든 API는 인증 필수 (로그인 페이지 제외)
- 작가 전용 API는 `role === 'artist'` 검증
- CSRF 토큰 검증 (Django 기본 제공)

#### 사용자 탈퇴 정책
- **일반 사용자 (스타일 미생성)**:
  - 즉시 탈퇴 가능
  - `users` 삭제 시 CASCADE로 관련 데이터 자동 삭제
  - 생성물, 댓글, 좋아요 등 모두 삭제됨

- **작가 (스타일 생성, 사용 내역 있음)**:
  - **물리 삭제 불가** (DB 제약조건: `styles → generations RESTRICT`)
  - 계정 비활성화 방식 사용:
    - `users.is_active = false` (소프트 삭제)
    - 로그인 차단, 프로필 숨김
    - 스타일 및 생성 이력 보존 (저작권 추적용)
  - 이유: 다른 사용자가 해당 스타일로 생성한 이미지의 메타데이터 보존 필요

- **작가 (스타일 미사용)**:
  - 스타일에 연결된 `generations`가 없으면 즉시 삭제 가능
  - Backend에서 `generations` COUNT 확인 후 처리

### 10.2 데이터 보호

#### 민감 정보 암호화
- **Google Secret Manager**: 민감 정보 암호화 저장
  - `SECRET_KEY`, `OAUTH_CLIENT_SECRET`, `INTERNAL_API_TOKEN`, `TOSS_SECRET_KEY`
  - Cloud Run에서 자동으로 환경 변수로 주입
- **환경 변수**: 비민감 정보 (`DATABASE_URL`, `RABBITMQ_HOST`, `GCS_BUCKET_NAME`)

#### Cloud Storage 접근 제어
- **서비스 계정 인증** (키 파일 불필요):
  - **Backend (Cloud Run)**: 서비스 계정에 Storage 권한 부여 (`roles/storage.objectAdmin`)
  - **AI Servers (GCE)**: VM에 연결된 서비스 계정으로 자동 인증
  - IAM으로 권한 세밀하게 제어 가능

#### 이미지 저장
- **학습 이미지**: `stylelicense-media` 버킷 (Private, 작가만 접근)
  - IAM 정책으로 특정 사용자만 읽기/쓰기 권한 부여
- **생성 이미지**: `stylelicense-generations` 버킷 (Public 읽기, 서명 포함)
  - 메타데이터: 작가 ID, 생성 시간, 스타일 ID 기록
  - 서명 없는 원본 이미지는 사용자 접근 불가
- **모델 파일**: `stylelicense-models` 버킷 (Private)
  - 학습된 LoRA 모델 (.safetensors) 저장

### 10.3 Rate Limiting

- **이미지 생성**: 1명당 6회/분
- **API 전체**: 1명당 100회/분
- **로그인 시도**: 1 IP당 5회/5분

### 10.4 입력 검증

- **Backend**: DRF Serializer 검증
- **Frontend**: Zod 런타임 검증
- **이미지 업로드**: 파일 형식, 크기, 해상도 검증
- **프롬프트**: XSS 방지 (HTML 태그 제거)

### 10.5 보안 헤더
```python
# Django settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True  # Production only
SESSION_COOKIE_SECURE = True  # Production only
CSRF_COOKIE_SECURE = True  # Production only
```

> **상세 보안 정책**: [docs/SECURITY.md](docs/SECURITY.md)

---

## 11. 에러 처리 및 로깅

### 11.1 에러 처리 전략

#### Backend (Django)
- **Global Exception Handler**: DRF의 `exception_handler` 커스터마이징
- **Business Logic Error**: 커스텀 Exception 클래스 사용
- **Unexpected Error**: 500 응답 + Sentry 전송

#### Frontend (Vue)
- **API Error Interceptor**: Axios response interceptor에서 일괄 처리
- **Component Error Boundary**: `errorCaptured` 훅 사용
- **User Feedback**: Toast 메시지 또는 Error 페이지

#### AI Servers (Python)
- **RabbitMQ Consumer Error**: Nack + 재시도 (최대 3회)
- **Training/Inference Failure**: Backend Webhook 호출 + 토큰 환불

### 11.2 로깅 전략

#### Backend
- **Access Log**: Django 기본 로깅 (INFO 레벨)
- **Error Log**: 모든 Exception (ERROR 레벨)
- **Business Log**: 토큰 트랜잭션, 모델 학습 시작/완료 (INFO 레벨)

#### AI Servers
- **Training Log**: 학습 진행률, loss, epoch (INFO 레벨)
- **Inference Log**: 이미지 생성 시간, 서명 삽입 성공 (INFO 레벨)

#### 로그 저장
- **Development**: 콘솔 출력
- **Production**: 파일 로그 + Sentry (Error만)

### 11.3 모니터링

- **Sentry**: 에러 추적 (Backend, Frontend)
- **CloudWatch** (AWS): 서버 리소스 모니터링
- **RabbitMQ Management UI**: 큐 길이, 처리 속도

---

## 12. 성능 및 확장성

### 12.1 성능 목표

| 지표 | 목표 |
|------|------|
| API 응답 시간 (p95) | < 500ms |
| 이미지 생성 시간 | < 10초/장 |
| 모델 학습 시간 | < 30분 (10장 기준) |
| 동시 접속자 | 100명 이상 |

### 12.2 데이터베이스 최적화

#### 인덱스 전략
- `User.google_id` - 고유 인덱스
- `StyleModel.training_status` - 필터링용
- `StyleModel.created_at` - 정렬용
- `GeneratedImage(user_id, created_at)` - 복합 인덱스
- `TokenTransaction(user_id, created_at)` - 복합 인덱스

#### 쿼리 최적화
- `select_related`: ForeignKey 조회 시
- `prefetch_related`: ManyToMany 조회 시
- Pagination: Cursor-based (offset 대신)

### 12.3 캐싱 전략

#### Redis 캐싱 (MVP 이후)
- 인기 모델 목록 (5분 TTL)
- 인기 태그 목록 (10분 TTL)
- 사용자 토큰 잔액 (Write-through cache)

### 12.4 이미지 최적화

- **학습 이미지**: 512x512로 리사이즈
- **생성 이미지**: WebP 형식 변환 (선택)
- **썸네일**: 256x256 자동 생성 (모델 목록용)

### 12.5 확장성 전략

#### Horizontal Scaling
- **Backend**: Stateless 설계로 인스턴스 추가 가능
- **AI Servers**: Worker 수평 확장 (RabbitMQ Queue 기반)

#### Vertical Scaling
- **PostgreSQL**: RDS 인스턴스 크기 증가
- **GPU Server**: 더 강력한 GPU로 업그레이드

#### Auto Scaling (향후)
- Backend: CPU 사용률 70% 이상 시 인스턴스 추가
- Inference Server: 큐 길이 100 이상 시 Worker 추가

---

## 13. 테스트 전략

### 13.1 테스트 피라미드
```
     /\
    /E2E\       10% - Playwright (Critical Path)
   /──────\
  /  통합  \     20% - API Integration Tests
 /──────────\
/   단위     \   70% - Unit Tests (Service, Model)
──────────────
```

### 13.2 Backend 테스트

#### Unit Tests
- **Models**: 필드 검증, 메서드 테스트
- **Services**: 비즈니스 로직 테스트 (TokenService, NotificationService)
- **Serializers**: 데이터 검증 테스트

#### Integration Tests
- **API Endpoints**: 모든 엔드포인트 응답 테스트
- **Database**: 트랜잭션, 동시성 테스트

#### 도구
- `pytest`, `pytest-django`
- Coverage 목표: 80%

### 13.3 Frontend 테스트

#### Unit Tests
- **Composables**: 재사용 로직 테스트
- **Stores**: Pinia 스토어 액션/게터 테스트
- **Utils**: 유틸리티 함수 테스트

#### Component Tests
- **UI Components**: Vitest + Testing Library

#### E2E Tests
- **Critical Path**: Playwright
  - 로그인 → 모델 검색 → 이미지 생성 → 다운로드
  - 모델 등록 → 학습 완료 → 알림 확인

#### 도구
- `Vitest`, `@testing-library/vue`, `Playwright`
- Coverage 목표: 70%

### 13.4 AI 서버 테스트

#### Unit Tests
- **Preprocessing**: 이미지 리사이즈, 포맷 변환
- **Signature Insertion**: 위치, 투명도, 크기 테스트

#### Integration Tests
- **RabbitMQ Consumer**: 메시지 수신 및 처리
- **API Callback**: Backend Webhook 호출 테스트

#### Manual Tests
- **Training**: 실제 10장 이미지로 학습 후 품질 확인
- **Inference**: 다양한 프롬프트로 생성 테스트

---

## 14. 배포 및 CI/CD

### 14.1 개발 환경

#### Docker Compose
```yaml
services:
  backend:
    build: ./apps/backend
    ports: ["8000:8000"]
  
  frontend:
    build: ./apps/frontend
    ports: ["3000:3000"]
  
  training-server:
    build: ./apps/training-server
    runtime: nvidia
  
  inference-server:
    build: ./apps/inference-server
    runtime: nvidia
  
  postgres:
    image: postgres:15
  
  rabbitmq:
    image: rabbitmq:3-management
```

### 14.2 프로덕션 환경

#### 인프라 (Google Cloud Platform 기준)

**전체 아키텍처**:
```
User → Cloud CDN → Cloud Storage (Frontend)
User → Cloud Run (Backend API)
  ↓
  ├─ Cloud SQL (PostgreSQL 15)
  ├─ RabbitMQ (GCE VM)
  └─ Cloud Storage (이미지/모델)
       ↓
  ┌────┴────┐
  ↓         ↓
Training   Inference
Server     Server
(GCE+GPU)  (GCE+GPU)
```

#### 서비스별 구성

##### 1. Backend (API Server)
- **서비스**: **Google Cloud Run** (서버리스 컨테이너)
- **설정**:
  - 최소 인스턴스: 1 (Cold start 방지)
  - 최대 인스턴스: 100 (자동 확장)
  - CPU: 1 vCPU
  - Memory: 512MB
  - Timeout: 300초
- **인증**: 서비스 계정 (Cloud SQL, Cloud Storage 권한 자동 부여)
- **배포**: `gcloud run deploy` 또는 Cloud Build
- **HTTPS**: 자동 SSL 인증서 발급
- **도메인**: Custom domain 매핑 가능 (예: api.stylelicense.com)

##### 2. Frontend (SPA)
- **서비스**: **Google Cloud Storage** (정적 호스팅) + **Cloud CDN**
- **설정**:
  - 버킷: `stylelicense-frontend`
  - 공개 읽기 권한 (allUsers)
  - Website 설정: index.html, error page: index.html (SPA 라우팅)
- **CDN**: Cloud CDN으로 글로벌 캐싱
  - Cache 정책: HTML (5분), JS/CSS/이미지 (1년)
- **HTTPS**: Google 관리 SSL 인증서 자동 발급
- **도메인**: Custom domain (예: www.stylelicense.com)

##### 3. Database
- **서비스**: **Google Cloud SQL** (PostgreSQL 15)
- **인스턴스 타입**:
  - **프로덕션**: db-n1-standard-2 (2 vCPU, 7.5GB RAM)
  - **개발/스테이징**: db-f1-micro (0.6GB RAM) - 비용 절감
- **스토리지**: 20GB SSD (자동 증가 활성화)
- **백업**: 자동 백업 (매일, 7일 보관)
- **고가용성**: 리전 내 HA (선택사항, 추가 비용)
- **연결**: Cloud Run → Cloud SQL Auth Proxy (자동, 암호화)

##### 4. Message Queue
- **서비스**: **RabbitMQ on GCE VM** (Docker 컨테이너)
- **머신 타입**: e2-medium (2 vCPU, 4GB RAM)
- **디스크**: 20GB Standard Persistent Disk
- **네트워크**: 내부 IP만 사용 (방화벽으로 5672 포트 제한)
- **배포**: Docker Compose 또는 단일 컨테이너
- **모니터링**: Management UI (http://<internal-ip>:15672)
- **향후 계획**: Cloud Pub/Sub로 마이그레이션 고려 (서버리스, HA 자동)

##### 5. AI Training Server
- **서비스**: **Google Compute Engine** (GPU VM)
- **머신 타입**: n2d-standard-4 (4 vCPU, 16GB RAM)
- **GPU**: NVIDIA L4 (24GB VRAM) 또는 T4 (16GB VRAM)
- **프로비저닝 모델**: **Spot (선점형)** - 비용 최대 70% 절감
  - 학습은 중단 후 재시작 가능하므로 Spot VM이 이상적
  - 체크포인트 자동 저장으로 진행률 손실 방지
- **부팅 디스크**: Deep Learning on Linux (CUDA 11.8+ 포함, 50GB)
- **서비스 계정**: Storage 객체 생성자/뷰어 권한
- **방화벽**: RabbitMQ VM (5672), Backend (443) 트래픽만 허용
- **배포**: Docker 컨테이너 (`docker run --gpus all`)

##### 6. AI Inference Server
- **서비스**: **Google Compute Engine** (GPU VM)
- **머신 타입**: n2d-standard-4 (4 vCPU, 16GB RAM)
- **GPU**: **NVIDIA T4 (16GB VRAM)** - 추론에 비용 효율적
- **프로비저닝 모델**: **Standard (표준)** + **1년 약정 사용 할인(CUD)**
  - 24/7 운영 필요, CUD로 최대 57% 비용 절감
- **부팅 디스크**: Deep Learning on Linux (CUDA 11.8+ 포함, 50GB)
- **서비스 계정**: Storage 객체 생성자/뷰어 권한
- **동시 처리**: MAX_CONCURRENT_GENERATIONS=10
- **배포**: Docker 컨테이너 (`docker run --gpus all`)

##### 7. Storage
- **서비스**: **Google Cloud Storage**
- **버킷 구조**:
  - `stylelicense-media`: 학습 이미지, 프로필 이미지
  - `stylelicense-models`: LoRA 모델 파일 (.safetensors)
  - `stylelicense-generations`: 생성된 이미지
- **스토리지 클래스**: Standard (자주 액세스)
- **인증**: 서비스 계정 (키 파일 불필요, IAM으로 권한 부여)
- **생명주기 정책**: 90일 이상 미사용 객체 → Nearline 이동 (비용 절감)

#### 비용 예상 (월간)
- Cloud Run (Backend): $20-50
- Cloud SQL (db-n1-standard-2): $100-150
- GCE Inference (T4 + CUD): $150-200
- GCE Training (L4 Spot): $50-100 (사용량에 따라)
- RabbitMQ VM (e2-medium): $30-40
- Cloud Storage: $10-30
- Cloud CDN: $5-20
- **총 예상: $365-590/월**

#### 네트워크 구성
- Cloud Run ↔ Cloud SQL: Private IP (Cloud SQL Connector)
- Cloud Run ↔ RabbitMQ: GCE 내부 IP (VPC 피어링 또는 Serverless VPC Access)
- AI Servers ↔ RabbitMQ: GCE 내부 IP (동일 VPC)
- AI Servers → Backend (Webhook): Public URL (HTTPS) + INTERNAL_API_TOKEN 인증

### 14.3 GCP 배포 가이드

각 서비스는 역할에 맞는 최적의 GCP 서비스에 개별적으로 배포됩니다:

**Backend 배포**:
- 서비스: **Cloud Run** (서버리스 컨테이너)
- 가이드: [apps/backend/README.md](apps/backend/README.md#deployment-gcp)
- 배포 명령어:
  ```bash
  # Docker 이미지 빌드 및 Cloud Run 배포
  gcloud builds submit --tag gcr.io/$PROJECT_ID/backend
  gcloud run deploy backend --image gcr.io/$PROJECT_ID/backend \
      --add-cloudsql-instances $SQL_INSTANCE \
      --set-env-vars="RABBITMQ_HOST=10.x.x.x,GCS_BUCKET_NAME=stylelicense-media"
  ```

**Frontend 배포**:
- 서비스: **Cloud Storage** + **Cloud CDN**
- 가이드: [apps/frontend/README.md](apps/frontend/README.md#deployment-gcp)
- 배포 명령어:
  ```bash
  # 정적 파일 빌드 및 Cloud Storage 업로드
  npm run build
  gcloud storage cp -r dist/* gs://stylelicense-frontend -m
  ```

**Database**:
- 서비스: **Cloud SQL** (PostgreSQL 15)
- 가이드: [docs/database/README.md](docs/database/README.md)
- 생성 명령어:
  ```bash
  gcloud sql instances create stylelicense-db \
      --database-version=POSTGRES_15 \
      --tier=db-n1-standard-2 \
      --region=asia-northeast3
  ```

**AI Servers** (Training/Inference):
- 서비스: **Google Compute Engine** (GPU VM)
- Training 가이드: [apps/training-server/README.md](apps/training-server/README.md#deployment)
- Inference 가이드: [apps/inference-server/README.md](apps/inference-server/README.md#deployment)
- 배포 명령어:
  ```bash
  # GCE GPU VM에서 Docker 컨테이너 실행
  docker run -d --gpus all \
      -e RABBITMQ_HOST=10.128.0.5 \
      -e GCS_BUCKET_NAME=stylelicense-media \
      -e INTERNAL_API_TOKEN=$TOKEN \
      stylelicense/training-server:latest
  ```

**로컬 개발 환경**:
- 루트의 `docker-compose.yml` 사용
- 가이드: [DOCKER.md](../../DOCKER.md)
- 실행 명령어:
  ```bash
  # 프로젝트 루트에서
  docker-compose up -d
  ```

### 14.4 CI/CD

#### 현재 배포 방식

**Backend (Cloud Run)**:
- 수동 배포: `gcloud builds submit` + `gcloud run deploy`
- 향후: GitHub Actions → Cloud Build → Cloud Run (자동 배포)

**Frontend (Cloud Storage)**:
- 수동 배포: `npm run build` + `gcloud storage cp`
- 향후: GitHub Actions → Cloud Storage + CDN Invalidation

**AI Servers (GCE)**:
- 수동 배포: SSH → Docker pull/build → 컨테이너 재시작
- 향후: GitHub Actions → Artifact Registry → GCE 자동 업데이트

#### 향후 CI/CD 파이프라인 계획

**1. Backend 파이프라인** (GitHub Actions):
```yaml
main 브랜치 push → Lint → Test → Build Docker Image →
Push to Artifact Registry → Deploy to Cloud Run → Health Check
```

**2. Frontend 파이프라인** (GitHub Actions):
```yaml
main 브랜치 push → Lint → Test → Build (npm run build) →
Upload to Cloud Storage → Invalidate CDN Cache
```

**3. AI Servers 파이프라인** (GitHub Actions):
```yaml
main 브랜치 push → Lint → Test → Build Docker Image →
Push to Artifact Registry →
SSH to GCE → Pull Image → Restart Container → Health Check
```

**배포 전략**:
- **Backend (Cloud Run)**: Blue-Green Deployment (트래픽 분산 배포)
- **Frontend (Cloud Storage)**: 캐시 무효화 후 즉시 배포
- **AI Servers**: Rolling Update (Training은 Spot VM이므로 중단 가능, Inference는 무중단)

### 14.5 환경 변수 관리

#### Development (로컬 환경)
- `.env.example` 템플릿 제공
- 로컬 `.env` 파일로 관리
- Git에 커밋하지 않음 (`.gitignore`에 포함)

#### Production (GCP)

**1. Google Secret Manager** (민감 정보):
```bash
# 민감 정보를 Secret Manager에 저장
gcloud secrets create DJANGO_SECRET_KEY --data-file=-
gcloud secrets create INTERNAL_API_TOKEN --data-file=-
gcloud secrets create GOOGLE_CLIENT_SECRET --data-file=-
gcloud secrets create TOSS_SECRET_KEY --data-file=-

# Cloud Run에서 Secret Manager 접근 (환경 변수로 자동 주입)
gcloud run deploy backend \
    --set-secrets="SECRET_KEY=DJANGO_SECRET_KEY:latest,INTERNAL_API_TOKEN=INTERNAL_API_TOKEN:latest"
```

**2. Cloud Run 환경 변수** (비민감 정보):
```bash
# 환경 변수 직접 설정 (비밀번호 등 민감 정보 제외)
gcloud run deploy backend \
    --set-env-vars="RABBITMQ_HOST=10.128.0.5,GCS_BUCKET_NAME=stylelicense-media,DEBUG=False"
```

**3. 서비스 계정 인증** (키 파일 불필요):
- Cloud Run, GCE VM에 서비스 계정을 연결하여 자동 인증
- **Cloud SQL**: Cloud SQL Auth Proxy로 자동 연결 (비밀번호 불필요)
- **Cloud Storage**: 서비스 계정에 Storage 권한 부여 (`roles/storage.objectAdmin`)
- **장점**: 키 파일 관리 불필요, 보안 강화, IAM으로 권한 제어

**환경 변수 우선순위**:
1. Secret Manager (민감 정보)
2. Cloud Run 환경 변수 (비민감 정보)
3. 서비스 계정 (인증 정보)

**주요 환경 변수 목록**:

| 환경 변수 | 관리 방식 | 설명 |
|----------|----------|------|
| `SECRET_KEY` | Secret Manager | Django Secret Key |
| `INTERNAL_API_TOKEN` | Secret Manager | AI 서버 Webhook 인증 |
| `GOOGLE_CLIENT_SECRET` | Secret Manager | OAuth2 Client Secret |
| `TOSS_SECRET_KEY` | Secret Manager | 결제 API Secret |
| `RABBITMQ_HOST` | 환경 변수 | RabbitMQ 내부 IP |
| `GCS_BUCKET_NAME` | 환경 변수 | Storage 버킷 이름 |
| `DEBUG` | 환경 변수 | Debug 모드 (False) |
| `DATABASE_URL` | 환경 변수 | Cloud SQL 연결 문자열 |
| `ALLOWED_HOSTS` | 환경 변수 | 허용 도메인 목록 |
| `CORS_ALLOWED_ORIGINS` | 환경 변수 | CORS 허용 도메인 |

---

## 15. 문서화 요구사항

### 15.1 문서 구조
```
project-root/
├── README.md              # 프로젝트 소개 (외부용)
├── TECHSPEC.md            # 이 문서 (전체 시스템 개요)
├── PLAN.md                # 개발 계획 및 진행 상황
├── claude.md              # Claude 작업 가이드
├── docs/
│   ├── database/
│   │   ├── README.md                # DB 개요, 전체 ERD, 설계 원칙
│   │   ├── guides/
│   │   │   ├── queries.md     (실전 쿼리 모음)
│   │   │   └── operations.md  (마이그레이션 + 운영)
│   │   └── TABLES.md          (모든 테이블 정의 한 곳에)
│   ├── API.md             # API 명세 상세
│   └── PATTERNS.md        # 코드 패턴
└── apps/
    ├── backend/           # 개발용 Backend 코드
    │   ├── README.md      # Backend 아키텍처
    │   ├── PLAN.md        # Backend 작업 계획
    │   └── CODE_GUIDE.md  # Backend 코드 가이드
    ├── frontend/          # 개발용 Frontend 코드
    │   ├── README.md
    │   ├── PLAN.md
    │   └── CODE_GUIDE.md
    ├── training-server/   # 학습 서버 코드
    │   ├── README.md
    │   ├── PLAN.md
    │   └── CODE_GUIDE.md
    └── inference-server/  # 추론 서버 코드
        ├── README.md
        ├── PLAN.md
        └── CODE_GUIDE.md
```

### 15.2 문서 작성 규칙

- **Markdown 형식** 사용
- **목차** 필수 포함
- **상호 참조** 명확히 (상대 경로 링크)
- **다이어그램** Mermaid 또는 ASCII Art
- **코드 예시** 언어 명시 (```python, ```javascript)

### 15.3 문서 업데이트 주기

- **TECHSPEC.md**: 아키텍처 변경 시
- **PLAN.md**: 매주 금요일 (진행 상황 반영)
- **API.md**: API 추가/변경 시 즉시
- **README.md**: 신규 기능 추가 시

---

## 16. 마이그레이션 계획

### 16.1 데이터베이스 마이그레이션

#### Django Migrations
- **초기 마이그레이션**: `python manage.py makemigrations` → `0001_initial.py`
- **스키마 변경**: 새 마이그레이션 파일 생성 → 프로덕션 적용 전 백업
- **롤백 계획**: `python manage.py migrate app_name previous_migration`

#### 마이그레이션 전략
1. 개발 환경에서 마이그레이션 테스트
2. 스테이징 환경 적용
3. 프로덕션 DB 백업
4. 프로덕션 적용 (점검 시간대)
5. 롤백 준비 (이전 마이그레이션 파일 보관)

### 16.2 코드 마이그레이션 (MVP 이후)

#### Python 버전 업그레이드
- 3.11 → 3.12: 호환성 테스트 후 점진적 적용

#### Django 버전 업그레이드
- 5.x → 6.x: Deprecation 경고 해결 후 업그레이드

#### Node.js 버전 업그레이드
- 20 LTS → 다음 LTS: 패키지 호환성 확인

---

## 17. 위험 요소 및 완화 전략

### 17.1 기술적 위험

| 위험 | 발생 확률 | 영향도 | 완화 전략 |
|------|-----------|--------|-----------|
| GPU 서버 비용 초과 | 중간 | 높음 | 사용량 모니터링, 배치 처리 최적화, 자동 스케일링 |
| 모델 학습 실패율 증가 | 낮음 | 중간 | 재시도 로직, 에러 로깅, 사전 이미지 검증 |
| 동시 접속 증가로 인한 성능 저하 | 중간 | 높음 | 부하 테스트, 캐싱, Auto Scaling 준비 |
| S3 비용 증가 | 중간 | 중간 | 이미지 압축, 오래된 이미지 자동 삭제 정책 |
| RabbitMQ 큐 적체 | 낮음 | 높음 | 큐 길이 모니터링, Worker 수평 확장 |

### 17.2 비즈니스 위험

| 위험 | 발생 확률 | 영향도 | 완화 전략 |
|------|-----------|--------|-----------|
| 저작권 분쟁 | 낮음 | 높음 | 서명 강제 삽입, 작가 신원 확인 강화 |
| 악의적 사용자 (스팸, 어뷰징) | 중간 | 중간 | Rate Limiting, 신고 시스템 구현 |
| 작가 이탈 (수익 불만) | 중간 | 높음 | 정산 시스템 투명화, 작가 대시보드 제공 |
| 법적 규제 변화 | 낮음 | 높음 | 법률 자문, ToS 업데이트 |

### 17.3 운영 위험

| 위험 | 발생 확률 | 영향도 | 완화 전략 |
|------|-----------|--------|-----------|
| 데이터베이스 장애 | 중간 | 치명적 | 정기적인 `pg_dump` 실행 및 백업 파일 S3 업로드 |
| GPU 서버 다운 | 중간 | 높음 | Health Check, 자동 재시작, 예비 서버 |
| 보안 침해 | 낮음 | 치명적 | 정기 보안 감사, HTTPS 강제, Rate Limiting |

---

## 18. 참고 자료

### 18.1 기술 문서
- [Django Documentation](https://docs.djangoproject.com/)
- [Vue 3 Documentation](https://vuejs.org/)
- [Stable Diffusion Documentation](https://github.com/CompVis/stable-diffusion)
- [LoRA Fine-tuning Guide](https://huggingface.co/docs/diffusers/training/lora)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)

### 18.2 프로젝트 관련 링크
- **Repository**: [GitHub](https://github.com/your-org/style-license) (작성 예정)
- **Figma Design**: [Figma Link](https://figma.com/...) (작성 예정)
- **API Docs (Swagger)**: [Swagger UI](https://api.stylelicense.com/docs/) (배포 후)

### 18.3 관련 논문 및 아티클
- LoRA: Low-Rank Adaptation of Large Language Models (arXiv:2106.09685)
- Stable Diffusion: High-Resolution Image Synthesis with Latent Diffusion Models

---

**문서 작성일**: 2025-10-27  
**최종 수정일**: 2025-10-27  
**작성자**: [Your Name]  
**검토자**: [Reviewer Name]