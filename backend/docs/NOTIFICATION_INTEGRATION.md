# Notification System Integration

## Overview

Sistem notifikasi terintegrasi dengan semua modul utama aplikasi untuk memberikan informasi real-time kepada pengguna tentang berbagai event.

## Event Types

### Stream Events
- `stream.started` - Stream dimulai
- `stream.ended` - Stream berakhir
- `stream.health_degraded` - Kualitas stream menurun
- `stream.disconnected` - Stream terputus
- `stream.reconnected` - Stream tersambung kembali

### Video Events
- `video.uploaded` - Video berhasil diupload
- `video.published` - Video dipublikasikan
- `video.processing_failed` - Pemrosesan video gagal

### Account Events
- `account.token_expiring` - Token OAuth akan expired
- `account.token_expired` - Token OAuth sudah expired
- `account.quota_warning` - Kuota API hampir habis

### Strike Events
- `strike.detected` - Strike terdeteksi
- `strike.resolved` - Strike diselesaikan

### Billing Events
- `payment.success` - Pembayaran berhasil
- `payment.failed` - Pembayaran gagal
- `subscription.activated` - Subscription aktif
- `subscription.cancelled` - Subscription dibatalkan
- `subscription.expiring` - Subscription akan expired
- `subscription.expired` - Subscription sudah expired
- `subscription.renewed` - Subscription diperpanjang

### System Events
- `system.error` - Error sistem
- `security.alert` - Alert keamanan
- `backup.completed` - Backup selesai
- `backup.failed` - Backup gagal

### Channel Events
- `comment.received` - Komentar baru
- `comment.moderation_required` - Komentar perlu moderasi
- `competitor.update` - Update kompetitor
- `channel.subscriber_milestone` - Milestone subscriber
- `channel.revenue_alert` - Alert revenue

## Integration Points

### Stream Module (`backend/app/modules/stream/service.py`)
- `start_stream()` - Mengirim notifikasi stream started
- `stop_stream()` - Mengirim notifikasi stream ended
- `handle_disconnection()` - Mengirim notifikasi stream disconnected

### Strike Module (`backend/app/modules/strike/service.py`)
- `create_strike()` - Mengirim notifikasi strike detected
- `sync_strikes()` - Mengirim notifikasi strike resolved

### Video Module (`backend/app/modules/video/tasks.py`)
- `upload_video_task()` - Mengirim notifikasi upload success/failed

### Billing Module (`backend/app/modules/billing/notifications.py`)
- `BillingNotificationService` - Semua notifikasi billing

### Account Module (`backend/app/modules/account/tasks.py`)
- `check_expiring_tokens()` - Notifikasi token expiring
- `check_expired_tokens()` - Notifikasi token expired
- `check_quota_usage()` - Notifikasi quota warning

## Notification Channels

1. **Email** - Menggunakan SMTP
2. **Telegram** - Menggunakan Bot API
3. **Slack** - Menggunakan Webhooks
4. **SMS** - Placeholder (perlu integrasi Twilio/AWS SNS)

## Background Tasks

Jalankan task notifikasi secara berkala:

```bash
# Jalankan semua notification tasks
python -m scripts.run_notification_tasks

# Jalankan billing tasks saja
python -m scripts.run_billing_tasks
```

## Frontend Integration

### Notification Center
- `frontend/src/components/dashboard/notification-center.tsx`
- Menampilkan notifikasi real-time dari API
- Polling setiap 30 detik

### Notification Settings
- `frontend/src/app/dashboard/settings/notifications/page.tsx`
- Konfigurasi channel (Email, Telegram)
- Preferensi event per channel

## API Endpoints

### Notifications
- `GET /notifications` - List notifikasi
- `GET /notifications/unread/count` - Jumlah unread
- `POST /notifications/{id}/read` - Mark as read
- `POST /notifications/read-all` - Mark all as read
- `DELETE /notifications/{id}` - Delete notification
- `DELETE /notifications/clear` - Clear all

### Preferences
- `GET /notifications/preferences/{user_id}` - Get preferences
- `POST /notifications/preferences` - Create preference
- `PUT /notifications/preferences/{id}` - Update preference
- `DELETE /notifications/preferences/{id}` - Delete preference

### Channels
- `GET /notifications/channels` - List channels
- `POST /notifications/channels/{type}` - Configure channel
- `POST /notifications/channels/{type}/test` - Test channel
- `DELETE /notifications/channels/{type}` - Disable channel
