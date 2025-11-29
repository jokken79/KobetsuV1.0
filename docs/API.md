# API Documentation

UNS Kobetsu Keiyakusho REST API ドキュメント

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API endpoints (except `/auth/login`) require JWT authentication.

### Headers
```
Authorization: Bearer <access_token>
```

---

## Auth Endpoints

### POST /auth/login

ユーザー認証

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### POST /auth/refresh

トークン更新

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

### GET /auth/me

現在のユーザー情報取得

**Response:**
```json
{
  "id": 1,
  "email": "admin@example.com",
  "full_name": "Admin User",
  "role": "admin",
  "is_active": true
}
```

---

## Kobetsu Keiyakusho Endpoints

### GET /kobetsu

契約書一覧取得（ページネーション対応）

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| skip | int | スキップ数 (default: 0) |
| limit | int | 取得件数 (default: 20, max: 100) |
| status | string | ステータスフィルター (draft/active/expired/cancelled/renewed) |
| factory_id | int | 工場IDフィルター |
| search | string | 契約番号・派遣先名検索 |
| start_date | date | 開始日フィルター |
| end_date | date | 終了日フィルター |
| sort_by | string | ソートフィールド (default: created_at) |
| sort_order | string | ソート順 (asc/desc) |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "contract_number": "KOB-202411-0001",
      "worksite_name": "トヨタ自動車株式会社 田原工場",
      "dispatch_start_date": "2024-12-01",
      "dispatch_end_date": "2025-11-30",
      "number_of_workers": 5,
      "status": "active",
      "created_at": "2024-11-25T10:00:00Z"
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 20,
  "has_more": true
}
```

### GET /kobetsu/stats

契約書統計取得

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| factory_id | int | 工場IDフィルター (optional) |

**Response:**
```json
{
  "total_contracts": 100,
  "active_contracts": 45,
  "expiring_soon": 8,
  "expired_contracts": 30,
  "draft_contracts": 15,
  "total_workers": 250
}
```

### GET /kobetsu/expiring

期限間近の契約書取得

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| days | int | 日数 (default: 30) |

### GET /kobetsu/{id}

契約書詳細取得

**Response:**
```json
{
  "id": 1,
  "contract_number": "KOB-202411-0001",
  "factory_id": 1,
  "contract_date": "2024-11-25",
  "dispatch_start_date": "2024-12-01",
  "dispatch_end_date": "2025-11-30",
  "work_content": "製造ライン作業、検品、梱包業務",
  "responsibility_level": "通常業務",
  "worksite_name": "トヨタ自動車株式会社 田原工場",
  "worksite_address": "愛知県田原市緑が浜2号1番地",
  "organizational_unit": "第1製造部",
  "supervisor_department": "製造部",
  "supervisor_position": "課長",
  "supervisor_name": "田中太郎",
  "work_days": ["月", "火", "水", "木", "金"],
  "work_start_time": "08:00:00",
  "work_end_time": "17:00:00",
  "break_time_minutes": 60,
  "hourly_rate": 1500,
  "overtime_rate": 1875,
  "haken_moto_complaint_contact": {
    "department": "人事部",
    "position": "課長",
    "name": "山田花子",
    "phone": "03-1234-5678"
  },
  "haken_saki_complaint_contact": {
    "department": "総務部",
    "position": "係長",
    "name": "佐藤次郎",
    "phone": "0531-23-4567"
  },
  "haken_moto_manager": {
    "department": "派遣事業部",
    "position": "部長",
    "name": "鈴木一郎",
    "phone": "03-1234-5678"
  },
  "haken_saki_manager": {
    "department": "人事部",
    "position": "部長",
    "name": "高橋三郎",
    "phone": "0531-23-4567"
  },
  "number_of_workers": 5,
  "status": "active",
  "created_at": "2024-11-25T10:00:00Z",
  "updated_at": "2024-11-25T10:00:00Z"
}
```

### POST /kobetsu

新規契約書作成

**Request:**
```json
{
  "factory_id": 1,
  "employee_ids": [1, 2, 3],
  "contract_date": "2024-11-25",
  "dispatch_start_date": "2024-12-01",
  "dispatch_end_date": "2025-11-30",
  "work_content": "製造ライン作業、検品、梱包業務",
  "responsibility_level": "通常業務",
  "worksite_name": "トヨタ自動車株式会社 田原工場",
  "worksite_address": "愛知県田原市緑が浜2号1番地",
  "supervisor_department": "製造部",
  "supervisor_position": "課長",
  "supervisor_name": "田中太郎",
  "work_days": ["月", "火", "水", "木", "金"],
  "work_start_time": "08:00",
  "work_end_time": "17:00",
  "break_time_minutes": 60,
  "hourly_rate": 1500,
  "overtime_rate": 1875,
  "haken_moto_complaint_contact": {
    "department": "人事部",
    "position": "課長",
    "name": "山田花子",
    "phone": "03-1234-5678"
  },
  "haken_saki_complaint_contact": {
    "department": "総務部",
    "position": "係長",
    "name": "佐藤次郎",
    "phone": "0531-23-4567"
  },
  "haken_moto_manager": {
    "department": "派遣事業部",
    "position": "部長",
    "name": "鈴木一郎",
    "phone": "03-1234-5678"
  },
  "haken_saki_manager": {
    "department": "人事部",
    "position": "部長",
    "name": "高橋三郎",
    "phone": "0531-23-4567"
  }
}
```

### PUT /kobetsu/{id}

契約書更新

**Request:**
```json
{
  "work_content": "更新された業務内容",
  "hourly_rate": 1600,
  "notes": "更新メモ"
}
```

### DELETE /kobetsu/{id}

契約書削除

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| hard | bool | 完全削除 (default: false, draftのみ可) |

### POST /kobetsu/{id}/activate

契約書有効化（draft → active）

### POST /kobetsu/{id}/renew

契約更新

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| new_end_date | date | 新しい終了日 (required) |

### POST /kobetsu/{id}/duplicate

契約書複製

### GET /kobetsu/{id}/employees

契約書の従業員ID一覧取得

### POST /kobetsu/{id}/employees/{employee_id}

従業員追加

### DELETE /kobetsu/{id}/employees/{employee_id}

従業員削除

### POST /kobetsu/{id}/generate-pdf

PDF/DOCX生成

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| format | string | 出力形式 (pdf/docx, default: pdf) |

**Response:** File download

### POST /kobetsu/{id}/sign

契約書署名

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| pdf_path | string | 署名済みPDFパス (required) |

### GET /kobetsu/{id}/download

署名済みPDFダウンロード

### GET /kobetsu/export/csv

CSVエクスポート

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | ステータスフィルター |
| factory_id | int | 工場IDフィルター |

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Contract with ID 123 not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "message": "Error description"
}
```

---

## Status Codes

| Status | Japanese | Description |
|--------|----------|-------------|
| draft | 下書き | 作成中、未確定 |
| active | 有効 | 有効な契約 |
| expired | 期限切れ | 派遣期間終了 |
| cancelled | キャンセル | 取り消し |
| renewed | 更新済み | 更新により新契約へ移行 |

---

## Rate Limiting

Currently no rate limiting is implemented.

## Versioning

API version is included in the URL path: `/api/v1/`
