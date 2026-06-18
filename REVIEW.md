# LOIVE 코드 리뷰 & 개선 목록

> 작성일: 2026-06-18  
> 스택: Django 6.0.6 / django-allauth / Tailwind CSS (CDN) / SQLite (개발)  
> 상태: MVP 개발 완료, 출시 전 점검 단계

---

## P0 — 버그 & 보안 취약점 (반드시 수정)

### 1. 비회원 예약 폼 접근 가능
- **파일**: `bookings/views.py` → `booking_form()`
- **현상**: `booking_form` 뷰에 `@login_required`가 없어서 비회원도 예약 폼 페이지 진입 가능. POST만 `is_authenticated` 체크하므로 비회원이 날짜/시간 선택 후 결제 버튼을 누르면 아무 반응 없이 새로고침됨 (UX 혼란).
- **수정**: 뷰 상단에 비로그인 시 `redirect(f"/accounts/login/?next=...")` 추가하거나 `@login_required` 적용.

### 2. 서버 측 금액/인원 검증 없음
- **파일**: `bookings/views.py:70-71, 86`
- **현상**:
  ```python
  adults = int(request.POST.get("adults", 1))
  children = int(request.POST.get("children", 0))
  total_amount = activity.price * adults
  ```
  클라이언트가 `adults=0`, `adults=-5`, `children=999`를 보내면 금액이 0원/음수가 되거나 잔여석을 초과함.
- **수정**: 서버에서 범위 검증:
  ```python
  adults = max(1, min(int(request.POST.get("adults", 1)), slot.remaining))
  children = max(0, min(int(request.POST.get("children", 0)), slot.remaining - adults))
  ```

### 3. `int()` 변환 에러 미처리 → 500 에러
- **파일**: `bookings/views.py:70-71`, `activities/views.py:118`, `core/partner_views.py:144`
- **현상**: 악의적 사용자가 `adults=abc`를 POST하면 `int()` → `ValueError` → 500 Internal Server Error.
- **수정**: `try/except ValueError` 감싸거나 Django Form 클래스 사용.

### 4. 예약 취소 시 슬롯 잔여석 미복구
- **파일**: `bookings/views.py` → `booking_cancel()`
- **현상**: 취소 시 `booking.status = CANCELLED`만 변경하고 `slot.remaining`을 복구하지 않음. 취소해도 다른 사용자가 해당 자리를 예약할 수 없음.
- **수정**:
  ```python
  with transaction.atomic():
      slot = ActivitySlot.objects.select_for_update().get(pk=booking.slot_id)
      slot.remaining = F("remaining") + booking.headcount
      slot.save(update_fields=["remaining"])
      booking.status = Booking.Status.CANCELLED
      booking.save(update_fields=["status", "updated_at"])
  ```

### 5. 리뷰 rating 범위 미검증
- **파일**: `activities/views.py:118`
- **현상**: `rating = int(request.POST.get("rating", 5))`에서 0, 100, -1 등 유효하지 않은 값 저장 가능.
- **수정**: `rating = max(1, min(5, int(...)))` 또는 모델 `clean()` 검증.

### 6. 파트너 뷰 입력값 검증 없음
- **파일**: `core/partner_views.py:144-148`
- **현상**: 액티비티 등록 시 `price=0`, `price=-100`, `capacity=0` 가능. 음수 가격의 액티비티가 승인되면 예약 시 음수 금액 발생.
- **수정**: 최소값 검증 추가 (`price >= 1000`, `capacity >= 1` 등).

---

## P1 — 설계 이슈 (강력 권장)

### 7. `@login_required` 적용 불일치
- **현상**: 인증이 필요한 뷰들의 보호 방식이 제각각:

| 뷰 | 보호 방식 | 비고 |
|---|---|---|
| `booking_detail` | `@login_required` | OK |
| `booking_cancel` | `@login_required` | OK |
| `booking_form` | 없음 (POST만 체크) | 문제 |
| `booking_history` | 없음 (빈 리스트 반환) | 문제 |
| `profile` | `is_authenticated` 수동 | 불일치 |
| `write_review` | `is_authenticated` 수동 | 불일치 |

- **수정**: 모든 인증 필요 뷰에 `@login_required` 통일. `login_url`과 `next` 파라미터 일관되게 설정.

### 8. Django Form 클래스 미사용
- **현상**: 모든 뷰에서 `request.POST.get()`으로 직접 파싱. 검증 로직 분산, 에러 메시지 불일치, 테스트 어려움.
- **관련 파일**: `bookings/views.py`, `activities/views.py`, `core/partner_views.py`, `core/views.py`
- **수정**: 최소한 `BookingForm`, `ReviewForm`, `ActivityForm` 등 Form 클래스 분리.

### 9. N+1 쿼리 (리뷰 별점 분포)
- **파일**: `activities/views.py:85-87`
- **현상**:
  ```python
  for s in range(1, 6):
      cnt = activity.reviews.filter(rating=s).count()  # 5번 쿼리
  ```
- **수정**: 한 번의 쿼리로 대체:
  ```python
  dist = dict(activity.reviews.values_list('rating').annotate(cnt=Count('id')).values_list('rating', 'cnt'))
  ```

### 10. 중복 제출 방지 없음
- **파일**: `bookings/views.py` → `booking_form()` POST 처리
- **현상**: 결제 버튼 더블클릭 시 동일 예약이 2건 생성될 수 있음. 현재 멱등성 키나 JS disable 처리 없음.
- **수정**: JS에서 submit 후 버튼 즉시 disable + 서버에서 idempotency key 체크.

### 11. PENDING 상태 미활용
- **파일**: `bookings/views.py:87`
- **현상**: 예약 생성 시 바로 `status=CONFIRMED`. 실제 결제 연동 시에는 `PENDING → 결제 성공 → CONFIRMED` 흐름이어야 함.
- **수정**: PG 연동 시 상태 전환 로직 추가.

### 12. wishlist_api 보호 없음
- **파일**: `core/views.py:104-129`
- **현상**: 인증 없이 누구나 호출 가능. `ids` 파라미터에 수백 개 ID를 넣으면 부하 발생 가능.
- **수정**: `ids` 개수 제한 (예: 50개) + rate limiting 고려.

---

## P2 — 누락 기능 (출시 전 구현 필요)

### 13. 실결제 PG 연동
- **현상**: 결제 UI만 있고 실제 PG 연동 없음 (카카오페이/토스페이 선택 가능하지만 클릭 시 바로 예약 확정).
- **필요**: 토스페이먼츠 또는 카카오페이 API 연동 → 결제 승인 콜백 → 예약 확정.

### 14. 환불 처리
- **현상**: 취소 시 `status=cancelled`만 변경. 실 환불 없음.
- **필요**: PG 환불 API 호출 + 환불 정책 (취소 수수료, 환불 불가 기간 등).

### 15. 예약 확인 알림
- **현상**: 예약/취소 시 알림 없음.
- **필요**: 이메일 발송 (예약 확인, 취소 확인, 이용 전날 리마인더). 카카오 알림톡 연동 추가 고려.

### 16. 소셜 로그인 UI
- **현상**: `settings.py`에 카카오/구글/네이버 provider 등록되어 있지만 로그인 페이지에 소셜 로그인 버튼 없음.
- **필요**: 로그인/회원가입 페이지에 소셜 로그인 버튼 + 각 provider 앱 키 설정.

### 17. 비밀번호 변경 & 회원 탈퇴
- **현상**: allauth가 기본 제공하지만 마이페이지 UI에서 연결 없음. 회원 탈퇴 기능 완전 부재.
- **필요**: 마이페이지에 비밀번호 변경 링크 + 계정 삭제 기능 (법적 의무).

### 18. 페이지네이션
- **현상**: 탐색 페이지에서 전체 액티비티를 한 번에 로드, 리뷰도 전체 로드.
- **필요**: 무한스크롤 또는 페이지네이션 적용 (액티비티 수 증가 시 성능 문제).

### 19. 파트너 가입 신청 플로우
- **현상**: Partner 모델은 있지만 가입 신청 UI 없음. DB에서 직접 생성해야 함.
- **필요**: 파트너 신청 폼 → 관리자 승인/반려 → 알림.

### 20. 관리자 액티비티 승인 UI
- **현상**: 액티비티 상태(draft/pending/approved/rejected) 변경은 Django admin에서만 가능.
- **필요**: 관리자 대시보드에서 심사 대기 목록 확인 + 승인/반려 처리.

### 21. 리뷰 수정/삭제
- **현상**: `update_or_create`로 리뷰 수정은 가능하지만 삭제 UI 없음.
- **필요**: 내 리뷰 삭제 버튼 + 확인 모달.

### 22. 신고/차단 기능
- **현상**: 부적절한 리뷰 신고 기능 없음.
- **필요**: 리뷰 신고 → 관리자 검토 → 비공개/삭제 처리.

---

## P3 — 법적/인프라 (출시 필수)

### 23. SECRET_KEY 하드코딩
- **파일**: `config/settings.py:13`
- **현상**: `default="django-insecure-dev-only-change-in-production"` — 프로덕션에서 .env 파일 없으면 이 값 사용.
- **수정**: 프로덕션 배포 시 반드시 환경변수로 교체. `default` 제거하고 없으면 에러 발생하도록 변경.

### 24. 개인정보처리방침 / 이용약관
- **현상**: 더미 텍스트 페이지.
- **필요**: 실제 법률 검토 후 작성. 전자상거래법/개인정보보호법 준수.

### 25. 통신판매업 신고
- **필요**: 결제 중개 시 통신판매업 신고 필수.

### 26. 배포 환경
- **현상**: 로컬 SQLite + `python manage.py runserver`.
- **필요**: PostgreSQL + gunicorn + nginx (또는 AWS Elastic Beanstalk / Railway 등 PaaS). 이미지 호스팅은 S3 + CloudFront.

### 27. Rate Limiting
- **현상**: 로그인/회원가입/API에 요청 제한 없음.
- **필요**: `django-ratelimit` 또는 nginx 레벨에서 rate limiting.

### 28. 로깅/모니터링
- **현상**: 별도 로깅 설정 없음.
- **필요**: Django logging 설정 + Sentry 등 에러 트래킹.

---

## 참고: 잘 된 부분

- 모델 설계: `TextChoices`, `UniqueConstraint`, `select_for_update` 등 Django best practice
- 프로젝트 구조: apps 분리 적절 (accounts/activities/bookings/payments/settlements/core)
- 파트너 접근 제어: `@partner_required` 데코레이터로 일관적 관리
- 프로덕션 보안 기본 설정: HSTS, SSL redirect, secure cookie 세팅 존재
- 예약 동시성 처리: `select_for_update` + `F()` expression으로 race condition 방어
- UI/UX 완성도: 모바일 퍼스트, 컬러 토큰 시스템, 일관된 디자인 언어

---

## 테스트 계정

| 구분 | 아이디 | 비밀번호 |
|------|--------|----------|
| 관리자 | admin | admin1234 |
| 일반 유저 | test@loive.kr | Test1234! |
| 파트너 | admin (is_partner) | admin1234 |

## 개발 서버 실행

```bash
cd LOIVE-django
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py runserver
```

접속: http://localhost:8000/  
관리자: http://localhost:8000/admin/  
파트너센터: http://localhost:8000/partner/
