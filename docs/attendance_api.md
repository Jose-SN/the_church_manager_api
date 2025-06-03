# Attendance API Documentation

This document provides an overview of the Attendance API endpoints and their usage.

## Base URL
All endpoints are prefixed with `/api/v1/attendance`.

## Authentication
All endpoints require authentication. Include a valid JWT token in the `Authorization` header:
```
Authorization: Bearer <your_token>
```

## Models

### Attendance
```typescript
{
  id: number;
  user_id: number;
  event_id: number | null;
  meeting_id: number | null;
  status: 'present' | 'absent' | 'late' | 'excused';
  notes: string | null;
  recorded_by: number | null;
  created_at: string;  // ISO 8601 datetime
  updated_at: string;  // ISO 8601 datetime
}
```

### AttendanceStats
```typescript
{
  total: number;
  present: number;
  absent: number;
  late: number;
  excused: number;
  percentage: number;
}
```

### AttendanceSummary
```typescript
{
  period: string;  // 'daily' | 'weekly' | 'monthly'
  date: string;    // Date in ISO format
  total: number;
  present: number;
  absent: number;
  late: number;
  excused: number;
  percentage: number;
}
```

## Endpoints

### Create Attendance Record
Create a new attendance record.

```http
POST /
```

**Request Body:**
```json
{
  "user_id": 1,
  "event_id": 1,
  "status": "present",
  "notes": "Optional notes"
}
```

**Response:**
- `201 Created`: Returns the created attendance record
- `400 Bad Request`: Invalid input data
- `403 Forbidden`: Not enough permissions

---

### Get Attendance Record
Get a specific attendance record by ID.

```http
GET /{attendance_id}
```

**Parameters:**
- `attendance_id` (path, required): ID of the attendance record

**Response:**
- `200 OK`: Returns the attendance record
- `403 Forbidden`: Not enough permissions
- `404 Not Found`: Attendance record not found

---

### List Attendance Records
List attendance records with optional filtering.

```http
GET /
```

**Query Parameters:**
- `user_id` (int, optional): Filter by user ID
- `event_id` (int, optional): Filter by event ID
- `meeting_id` (int, optional): Filter by meeting ID
- `start_date` (datetime, optional): Filter by start date
- `end_date` (datetime, optional): Filter by end date
- `skip` (int, default=0): Number of records to skip
- `limit` (int, default=100): Maximum number of records to return

**Response:**
- `200 OK`: Returns a list of attendance records

---

### Update Attendance Record
Update an existing attendance record.

```http
PUT /{attendance_id}
```

**Parameters:**
- `attendance_id` (path, required): ID of the attendance record

**Request Body:**
```json
{
  "status": "absent",
  "notes": "Updated notes"
}
```

**Response:**
- `200 OK`: Returns the updated attendance record
- `403 Forbidden`: Not enough permissions
- `404 Not Found`: Attendance record not found

---

### Delete Attendance Record
Delete an attendance record.

```http
DELETE /{attendance_id}
```

**Parameters:**
- `attendance_id` (path, required): ID of the attendance record

**Response:**
- `204 No Content`: Record deleted successfully
- `403 Forbidden`: Not enough permissions
- `404 Not Found`: Attendance record not found

---

### Get Event Attendance Statistics
Get attendance statistics for a specific event.

```http
GET /event/{event_id}/stats
```

**Parameters:**
- `event_id` (path, required): ID of the event

**Response:**
- `200 OK`: Returns attendance statistics
- `404 Not Found`: Event not found

---

### Get Attendance Summary
Get attendance summary by period (daily, weekly, or monthly).

```http
GET /summary/
```

**Query Parameters:**
- `organization_id` (int, required): ID of the organization
- `start_date` (datetime, optional): Start date for the summary
- `end_date` (datetime, optional): End date for the summary
- `period` (string, default="daily"): Period for grouping (daily, weekly, monthly)

**Response:**
- `200 OK`: Returns a list of attendance summaries
- `403 Forbidden`: Only accessible by superusers

---

### Get Not Attended Users
Get users who did not attend a specific event.

```http
GET /event/{event_id}/not-attended/
```

**Parameters:**
- `event_id` (path, required): ID of the event
- `status` (string, default="absent"): Status to filter by (present, absent, late, excused)

**Response:**
- `200 OK`: Returns a list of users who did not attend

---

### Bulk Create Attendance Records
Create multiple attendance records at once.

```http
POST /bulk/
```

**Request Body:**
```json
[
  {
    "user_id": 1,
    "event_id": 1,
    "status": "present"
  },
  {
    "user_id": 2,
    "event_id": 1,
    "status": "absent"
  }
]
```

**Response:**
- `201 Created`: Returns a list of created attendance records
- `400 Bad Request`: Invalid input data
- `403 Forbidden`: Only accessible by admins
