# LOIVE Django 프로젝트 진행 상황

마지막 업데이트: 2026-06-18

## 현재 상태
- Django 6.0.6 프로젝트 초기 세팅 완료
- Python 3.14.4, venv 가상환경
- `python manage.py runserver 8000` 정상 가동 (http://localhost:8000)
- Admin 패널 정상 (http://localhost:8000/admin/ — admin / admin1234)
- **Next.js 원본과 색상 토큰 일치 완료** (TIDE 디자인 시스템: coral, ocean-blue, primary 등)

## 완료 항목

### 프로젝트 구조
- `config/` — Django 설정 (settings, urls, wsgi)
- `accounts/` — User(커스텀), Partner 모델
- `activities/` — Category, Region, Activity, ActivitySlot, Course, Review 모델
- `bookings/` — Booking 모델
- `payments/` — Payment, WebhookLog 모델
- `settlements/` — Settlement 모델
- `core/` — 홈페이지 뷰, 공통 기능, 파트너 뷰
- `templates/` — base.html, 네비게이션, 전체 페이지

### 설정
- django-allauth 연동 (카카오/구글/네이버 소셜 로그인 준비)
- django-environ (.env 파일 기반 환경변수)
- whitenoise (정적 파일 서빙)
- Pretendard 폰트 + Tailwind CSS CDN
- LOIVE 디자인 토큰 적용 (**TIDE 디자인 시스템 — Next.js 원본과 동일**)
- 보안 설정 (production 시 HTTPS 강제, 세션 보안, HSTS)
- Admin 커스터마이징 (파트너 승인/반려, 액티비티 승인/반려 액션)

### 데이터 모델 (요구사항.md 6장 완전 매칭)
- User: role(customer/partner/admin), phone
- Partner: 사업자정보, 정산계좌, 승인상태
- Activity: 카테고리, 지역, 가격, 정원, 위치, 승인상태, ActivityImage
- ActivitySlot: 날짜/시간/잔여정원 (unique constraint)
- Course: M2M Activity, 가격, 노출여부
- Booking: 예약번호, 인원, 금액, 상태
- Payment: PG 결제키, 결제수단, 웹훅로그
- Settlement: 파트너별 정산, 매출/수수료/정산액
- Review: 평점, 내용, 유저당 1회 제한

### 페이지 (전체 구현 상태)

#### 고객 — 메인
| 페이지 | 경로 | 상태 |
|---|---|---|
| 홈 | `/` | ✅ 완료 (배너, 카테고리, 인기 액티비티, 코스) |
| 탐색 | `/activities/` | ✅ 완료 (카테고리/지역/정렬 필터) |
| 검색 | `/search/` | ✅ 완료 |
| 상세 | `/activities/<id>/` | ✅ 완료 (리뷰, 슬롯, 관련 액티비티) |
| 코스 상세 | `/activities/course/<id>/` | ✅ 완료 |

#### 고객 — 예약
| 페이지 | 경로 | 상태 |
|---|---|---|
| 예약 폼 | `/bookings/<id>/` | ✅ 완료 (날짜/시간 선택, 인원, 동시성 제어) |
| 예약 완료 | `/bookings/<id>/complete/` | ✅ 완료 |
| 예약 내역 | `/bookings/` | ✅ 완료 (탭: 확정/완료/취소) |
| 예약 상세 | `/bookings/detail/<pk>/` | ✅ 완료 |
| 예약 취소 | `/bookings/detail/<pk>/cancel/` | ✅ 완료 (사유 선택, 환불 규정) |

#### 고객 — 리뷰
| 페이지 | 경로 | 상태 |
|---|---|---|
| 리뷰 목록 | `/activities/<id>/reviews/` | ✅ 완료 (평점 요약, 필터 칩) |
| 리뷰 작성 | `/activities/<id>/review/` | ✅ 완료 (별점 선택, 텍스트 입력) |

#### 고객 — 계정
| 페이지 | 경로 | 상태 |
|---|---|---|
| 로그인 | `/accounts/login/` | ✅ 완료 (이메일 + 소셜 로그인 대기) |
| 회원가입 | `/accounts/signup/` | ✅ 완료 |
| 로그아웃 | `/accounts/logout/` | ✅ 완료 |
| 비밀번호 찾기 | `/accounts/password/reset/` | ✅ 완료 |
| 프로필 | `/profile/` | ✅ 완료 (Quick Stats, 메뉴 그룹, 로그아웃) |
| 프로필 수정 | `/profile/edit/` | ✅ 완료 (이름/연락처 변경) |

#### 고객 — 부가
| 페이지 | 경로 | 상태 |
|---|---|---|
| 위시리스트 | `/wishlist/` | ✅ 완료 (localStorage 기반 찜 + API 연동) |
| 알림 | `/notifications/` | ✅ 완료 |
| FAQ/고객센터 | `/faq/` | ✅ 완료 (아코디언, 카테고리 필터) |
| 이용약관 | `/terms/` | ✅ 완료 |
| 개인정보처리방침 | `/privacy/` | ✅ 완료 |

#### 파트너센터
| 페이지 | 경로 | 상태 |
|---|---|---|
| 대시보드 | `/partner/` | ✅ 완료 (매출, 예약, 평점 통계) |
| 액티비티 목록 | `/partner/activities/` | ✅ 완료 (상태별 필터, 테이블) |
| 액티비티 등록 | `/partner/activities/new/` | ✅ 완료 (폼, 미리보기) |
| 액티비티 수정 | `/partner/activities/<pk>/edit/` | ✅ 완료 |
| 슬롯 관리 | `/partner/activities/<pk>/slots/` | ✅ 완료 (날짜별 그룹, 추가/삭제) |
| 예약 관리 | `/partner/bookings/` | ✅ 완료 (상태별 필터) |
| 정산 내역 | `/partner/settlements/` | ✅ 완료 (요약 카드, 이력 테이블) |

#### 공통
| 페이지 | 상태 |
|---|---|
| 404 에러 | ✅ 완료 |
| 500 에러 | ✅ 완료 |

## 다음 액션 (요구사항.md 7장 순서 기준)
1. ~~Django 프로젝트 초기 세팅~~ ✅
2. ~~인증 구현~~ ✅ (이메일 로그인 완료, 소셜 로그인은 SocialApp 등록 시 자동 활성화)
3. ~~Activity 등록/승인 플로우~~ ✅ (파트너용 액티비티 등록/수정 폼, 슬롯 관리)
4. ~~Booking 생성 로직~~ ✅ (기본 동작 완료)
5. 토스페이먼츠 결제 연동
6. 정산 로직 강화
7. ~~마이페이지 (파트너 대시보드)~~ ✅
8. Django Admin 고도화
9. Render 배포
10. 보안 점검

### 잔여 세부 작업
- 위시리스트: 상세 페이지/탐색 페이지에 하트 토글 버튼 추가
- 상세 페이지: 갤러리 이미지, 일정표(Itinerary), 안전 배지
- 예약 폼: 결제수단 선택, 약관 동의 체크박스
- 코스 카드: 태그 아이콘 (walk/food/drink/sail)
- 지역 선택 드롭다운 (한국 지도 SVG)

## 참고
- 기존 Next.js 프로젝트(`~/Desktop/LOIVE/`)는 디자인 레퍼런스로 보존
- 디자인 토큰: `stitch_/stitch_/tide/DESIGN.md` 참고
- 요구사항: `~/Desktop/요구사항.md`
