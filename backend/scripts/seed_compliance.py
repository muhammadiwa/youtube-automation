"""Seed script for compliance data.

Creates sample Terms of Service versions and Compliance Reports for testing.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

# Import all models to ensure they are registered
from app.modules.auth.models import User
from app.modules.admin.models import (
    Admin,
    TermsOfService,
    TermsOfServiceStatus,
    ComplianceReport,
    ComplianceReportStatus,
    ComplianceReportType,
)
from app.core.database import async_session_maker


TERMS_OF_SERVICE_CONTENT_V1 = """
# Syarat dan Ketentuan Layanan
## YouTube Automation Platform

**Terakhir diperbarui: 1 Oktober 2024**

### 1. Penerimaan Ketentuan

Dengan mengakses atau menggunakan YouTube Automation Platform ("Platform"), Anda setuju untuk terikat oleh Syarat dan Ketentuan ini. Jika Anda tidak setuju dengan ketentuan ini, mohon untuk tidak menggunakan Platform.

### 2. Deskripsi Layanan

Platform menyediakan layanan otomatisasi YouTube termasuk:
- Manajemen multi-akun YouTube
- Penjadwalan upload video otomatis
- Live streaming otomatis dengan playlist
- Generasi thumbnail menggunakan AI
- Analitik dan pelaporan performa

### 3. Akun Pengguna

3.1. Anda harus berusia minimal 18 tahun untuk menggunakan Platform.
3.2. Anda bertanggung jawab menjaga kerahasiaan kredensial akun Anda.
3.3. Anda bertanggung jawab atas semua aktivitas yang terjadi di akun Anda.

### 4. Penggunaan yang Dilarang

Anda dilarang menggunakan Platform untuk:
- Melanggar Ketentuan Layanan YouTube
- Menyebarkan konten ilegal, berbahaya, atau menyesatkan
- Spam atau aktivitas yang mengganggu
- Mengakses sistem tanpa izin

### 5. Pembayaran dan Langganan

5.1. Biaya langganan ditagih sesuai paket yang dipilih.
5.2. Pembayaran tidak dapat dikembalikan kecuali dinyatakan lain.
5.3. Kami berhak mengubah harga dengan pemberitahuan 30 hari sebelumnya.

### 6. Privasi Data

Penggunaan data Anda diatur oleh Kebijakan Privasi kami yang merupakan bagian dari Ketentuan ini.

### 7. Batasan Tanggung Jawab

Platform disediakan "sebagaimana adanya" tanpa jaminan apapun. Kami tidak bertanggung jawab atas kerugian tidak langsung yang timbul dari penggunaan Platform.

### 8. Perubahan Ketentuan

Kami dapat mengubah Ketentuan ini kapan saja. Perubahan material akan diberitahukan melalui email atau notifikasi di Platform.

### 9. Hukum yang Berlaku

Ketentuan ini diatur oleh hukum Republik Indonesia.

### 10. Kontak

Untuk pertanyaan tentang Ketentuan ini, hubungi: legal@youtubeautomation.com
"""

TERMS_OF_SERVICE_CONTENT_V2 = """
# Syarat dan Ketentuan Layanan
## YouTube Automation Platform

**Versi 2.0 - Berlaku sejak: 1 Desember 2024**

### 1. Penerimaan Ketentuan

Dengan mengakses atau menggunakan YouTube Automation Platform ("Platform"), Anda setuju untuk terikat oleh Syarat dan Ketentuan ini. Jika Anda tidak setuju dengan ketentuan ini, mohon untuk tidak menggunakan Platform.

### 2. Deskripsi Layanan

Platform menyediakan layanan otomatisasi YouTube termasuk:
- Manajemen multi-akun YouTube
- Penjadwalan upload video otomatis
- Live streaming otomatis dengan playlist
- Generasi thumbnail menggunakan AI
- Generasi judul dan deskripsi menggunakan AI
- Analitik dan pelaporan performa
- Moderasi chat otomatis
- Integrasi multi-platform streaming

### 3. Akun Pengguna

3.1. Anda harus berusia minimal 18 tahun untuk menggunakan Platform.
3.2. Anda bertanggung jawab menjaga kerahasiaan kredensial akun Anda.
3.3. Anda bertanggung jawab atas semua aktivitas yang terjadi di akun Anda.
3.4. Satu akun hanya boleh digunakan oleh satu individu atau entitas.

### 4. Penggunaan yang Dilarang

Anda dilarang menggunakan Platform untuk:
- Melanggar Ketentuan Layanan YouTube atau platform streaming lainnya
- Menyebarkan konten ilegal, berbahaya, atau menyesatkan
- Spam atau aktivitas yang mengganggu
- Mengakses sistem tanpa izin
- Menjual kembali layanan tanpa izin tertulis
- Menggunakan bot atau script otomatis di luar fitur Platform

### 5. Pembayaran dan Langganan

5.1. Biaya langganan ditagih sesuai paket yang dipilih (bulanan atau tahunan).
5.2. Pembayaran tidak dapat dikembalikan kecuali dinyatakan lain.
5.3. Kami berhak mengubah harga dengan pemberitahuan 30 hari sebelumnya.
5.4. Kegagalan pembayaran dapat mengakibatkan penangguhan layanan.

### 6. Privasi Data dan GDPR

6.1. Penggunaan data Anda diatur oleh Kebijakan Privasi kami.
6.2. Anda berhak meminta ekspor data pribadi Anda.
6.3. Anda berhak meminta penghapusan akun dan data Anda.
6.4. Kami memproses data sesuai dengan GDPR dan regulasi privasi yang berlaku.

### 7. Keamanan

7.1. Kami menerapkan enkripsi end-to-end untuk data sensitif.
7.2. Autentikasi dua faktor (2FA) tersedia dan direkomendasikan.
7.3. Kami melakukan audit keamanan secara berkala.

### 8. Batasan Tanggung Jawab

Platform disediakan "sebagaimana adanya" tanpa jaminan apapun. Kami tidak bertanggung jawab atas:
- Kerugian tidak langsung yang timbul dari penggunaan Platform
- Tindakan YouTube atau platform pihak ketiga terhadap akun Anda
- Downtime yang disebabkan oleh pemeliharaan terjadwal

### 9. Penghentian Layanan

9.1. Anda dapat membatalkan langganan kapan saja.
9.2. Kami dapat menangguhkan atau menghentikan akun yang melanggar Ketentuan ini.
9.3. Data akan disimpan selama 30 hari setelah penghentian akun.

### 10. Perubahan Ketentuan

Kami dapat mengubah Ketentuan ini kapan saja. Perubahan material akan diberitahukan melalui email atau notifikasi di Platform. Penggunaan berkelanjutan setelah perubahan berarti Anda menerima ketentuan baru.

### 11. Hukum yang Berlaku

Ketentuan ini diatur oleh hukum Republik Indonesia. Sengketa akan diselesaikan melalui arbitrase di Jakarta.

### 12. Kontak

Untuk pertanyaan tentang Ketentuan ini, hubungi:
- Email: legal@youtubeautomation.com
- Support: support@youtubeautomation.com
"""


async def seed_terms_of_service():
    """Seed sample Terms of Service versions."""
    async with async_session_maker() as session:
        # Check if ToS already exist
        result = await session.execute(select(TermsOfService).limit(1))
        if result.scalar_one_or_none():
            print("Terms of Service already exist. Skipping seed.")
            return 0

        # Get first admin for created_by (optional)
        admin_result = await session.execute(select(Admin).limit(1))
        admin = admin_result.scalar_one_or_none()
        admin_id = admin.user_id if admin else None

        now = datetime.utcnow()

        terms_versions = [
            TermsOfService(
                version="1.0.0",
                title="Syarat dan Ketentuan Layanan",
                content=TERMS_OF_SERVICE_CONTENT_V1,
                content_html=None,
                summary="Versi awal Terms of Service untuk YouTube Automation Platform",
                status=TermsOfServiceStatus.ARCHIVED.value,
                effective_date=now - timedelta(days=90),
                created_by=admin_id,
                activated_by=admin_id,
                activated_at=now - timedelta(days=90),
            ),
            TermsOfService(
                version="2.0.0",
                title="Syarat dan Ketentuan Layanan",
                content=TERMS_OF_SERVICE_CONTENT_V2,
                content_html=None,
                summary="Update: Penambahan ketentuan GDPR, keamanan, dan fitur baru AI",
                status=TermsOfServiceStatus.ACTIVE.value,
                effective_date=now - timedelta(days=14),
                created_by=admin_id,
                activated_by=admin_id,
                activated_at=now - timedelta(days=14),
            ),
            TermsOfService(
                version="2.1.0",
                title="Syarat dan Ketentuan Layanan",
                content=TERMS_OF_SERVICE_CONTENT_V2 + "\n\n### 13. Ketentuan Tambahan\n\n(Draft - dalam review)",
                content_html=None,
                summary="Draft: Penambahan ketentuan untuk fitur multi-platform streaming",
                status=TermsOfServiceStatus.DRAFT.value,
                effective_date=None,
                created_by=admin_id,
                activated_by=None,
                activated_at=None,
            ),
        ]

        for terms in terms_versions:
            session.add(terms)

        await session.commit()
        print(f"Successfully seeded {len(terms_versions)} Terms of Service versions.")
        return len(terms_versions)


async def seed_compliance_reports():
    """Seed sample Compliance Reports."""
    async with async_session_maker() as session:
        # Check if reports already exist
        result = await session.execute(select(ComplianceReport).limit(1))
        if result.scalar_one_or_none():
            print("Compliance Reports already exist. Skipping seed.")
            return 0

        # Get first admin for generated_by (optional)
        admin_result = await session.execute(select(Admin).limit(1))
        admin = admin_result.scalar_one_or_none()
        admin_id = admin.user_id if admin else None

        now = datetime.utcnow()

        # Use a default UUID if no admin exists
        default_user_id = admin_id if admin_id else uuid.uuid4()

        reports = [
            ComplianceReport(
                report_type=ComplianceReportType.GDPR_COMPLIANCE.value,
                title="GDPR Compliance Report Q3 2024",
                description="Laporan kepatuhan GDPR untuk kuartal 3 tahun 2024",
                status=ComplianceReportStatus.COMPLETED.value,
                start_date=now - timedelta(days=120),
                end_date=now - timedelta(days=30),
                parameters={"include_user_data": True, "include_consent_logs": True},
                file_path="/reports/gdpr_q3_2024.pdf",
                file_size=1024 * 512,  # 512 KB
                error_message=None,
                requested_by=default_user_id,
                completed_at=now - timedelta(days=25),
            ),
            ComplianceReport(
                report_type=ComplianceReportType.SECURITY_AUDIT.value,
                title="Security Audit Report November 2024",
                description="Audit keamanan sistem bulanan",
                status=ComplianceReportStatus.COMPLETED.value,
                start_date=now - timedelta(days=60),
                end_date=now - timedelta(days=30),
                parameters={"include_vulnerability_scan": True, "include_access_logs": True},
                file_path="/reports/security_audit_nov_2024.pdf",
                file_size=1024 * 256,  # 256 KB
                error_message=None,
                requested_by=default_user_id,
                completed_at=now - timedelta(days=28),
            ),
            ComplianceReport(
                report_type=ComplianceReportType.USER_ACTIVITY.value,
                title="User Activity Report Q4 2024",
                description="Laporan aktivitas pengguna untuk kuartal 4 tahun 2024",
                status=ComplianceReportStatus.COMPLETED.value,
                start_date=now - timedelta(days=90),
                end_date=now - timedelta(days=1),
                parameters={"include_login_history": True, "include_api_usage": True},
                file_path="/reports/user_activity_q4_2024.pdf",
                file_size=1024 * 1024,  # 1 MB
                error_message=None,
                requested_by=default_user_id,
                completed_at=now - timedelta(days=1),
            ),
            ComplianceReport(
                report_type=ComplianceReportType.DATA_PROCESSING.value,
                title="Data Processing Activities Report 2024",
                description="Laporan aktivitas pemrosesan data tahunan",
                status=ComplianceReportStatus.GENERATING.value,
                start_date=now - timedelta(days=365),
                end_date=now,
                parameters={"include_third_party": True, "include_data_transfers": True},
                file_path=None,
                file_size=None,
                error_message=None,
                requested_by=default_user_id,
            ),
            ComplianceReport(
                report_type=ComplianceReportType.FULL_AUDIT.value,
                title="Full Audit Report 2024",
                description="Laporan audit lengkap untuk tahun 2024",
                status=ComplianceReportStatus.PENDING.value,
                start_date=now - timedelta(days=365),
                end_date=now,
                parameters={"comprehensive": True},
                file_path=None,
                file_size=None,
                error_message=None,
                requested_by=default_user_id,
            ),
            ComplianceReport(
                report_type=ComplianceReportType.SECURITY_AUDIT.value,
                title="Security Audit Report October 2024",
                description="Audit keamanan sistem bulanan - gagal karena timeout",
                status=ComplianceReportStatus.FAILED.value,
                start_date=now - timedelta(days=90),
                end_date=now - timedelta(days=60),
                parameters={"include_vulnerability_scan": True},
                file_path=None,
                file_size=None,
                error_message="Report generation timed out after 30 minutes. Please try again.",
                requested_by=default_user_id,
            ),
        ]

        for report in reports:
            session.add(report)

        await session.commit()
        print(f"Successfully seeded {len(reports)} Compliance Reports.")
        return len(reports)


async def main():
    """Run all compliance seed functions."""
    print("=" * 50)
    print("Seeding Compliance Data")
    print("=" * 50)
    
    tos_count = await seed_terms_of_service()
    reports_count = await seed_compliance_reports()
    
    print("=" * 50)
    print(f"Seeding complete!")
    print(f"- Terms of Service: {tos_count} versions")
    print(f"- Compliance Reports: {reports_count} reports")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
