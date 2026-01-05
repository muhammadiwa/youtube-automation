"""Seed script for compliance data.

Creates sample Terms of Service versions and Compliance Reports for testing.

Run with: python -m scripts.seed_compliance
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


# ============================================================================
# TERMS OF SERVICE CONTENT - VERSION 1.0.0 (Archived)
# ============================================================================

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

TERMS_OF_SERVICE_HTML_V1 = """
<h1>Syarat dan Ketentuan Layanan</h1>
<h2>YouTube Automation Platform</h2>

<p><strong>Terakhir diperbarui: 1 Oktober 2024</strong></p>

<h3>1. Penerimaan Ketentuan</h3>
<p>Dengan mengakses atau menggunakan YouTube Automation Platform ("Platform"), Anda setuju untuk terikat oleh Syarat dan Ketentuan ini. Jika Anda tidak setuju dengan ketentuan ini, mohon untuk tidak menggunakan Platform.</p>

<h3>2. Deskripsi Layanan</h3>
<p>Platform menyediakan layanan otomatisasi YouTube termasuk:</p>
<ul>
    <li>Manajemen multi-akun YouTube</li>
    <li>Penjadwalan upload video otomatis</li>
    <li>Live streaming otomatis dengan playlist</li>
    <li>Generasi thumbnail menggunakan AI</li>
    <li>Analitik dan pelaporan performa</li>
</ul>

<h3>3. Akun Pengguna</h3>
<p>3.1. Anda harus berusia minimal 18 tahun untuk menggunakan Platform.</p>
<p>3.2. Anda bertanggung jawab menjaga kerahasiaan kredensial akun Anda.</p>
<p>3.3. Anda bertanggung jawab atas semua aktivitas yang terjadi di akun Anda.</p>

<h3>4. Penggunaan yang Dilarang</h3>
<p>Anda dilarang menggunakan Platform untuk:</p>
<ul>
    <li>Melanggar Ketentuan Layanan YouTube</li>
    <li>Menyebarkan konten ilegal, berbahaya, atau menyesatkan</li>
    <li>Spam atau aktivitas yang mengganggu</li>
    <li>Mengakses sistem tanpa izin</li>
</ul>

<h3>5. Pembayaran dan Langganan</h3>
<p>5.1. Biaya langganan ditagih sesuai paket yang dipilih.</p>
<p>5.2. Pembayaran tidak dapat dikembalikan kecuali dinyatakan lain.</p>
<p>5.3. Kami berhak mengubah harga dengan pemberitahuan 30 hari sebelumnya.</p>

<h3>6. Privasi Data</h3>
<p>Penggunaan data Anda diatur oleh Kebijakan Privasi kami yang merupakan bagian dari Ketentuan ini.</p>

<h3>7. Batasan Tanggung Jawab</h3>
<p>Platform disediakan "sebagaimana adanya" tanpa jaminan apapun. Kami tidak bertanggung jawab atas kerugian tidak langsung yang timbul dari penggunaan Platform.</p>

<h3>8. Perubahan Ketentuan</h3>
<p>Kami dapat mengubah Ketentuan ini kapan saja. Perubahan material akan diberitahukan melalui email atau notifikasi di Platform.</p>

<h3>9. Hukum yang Berlaku</h3>
<p>Ketentuan ini diatur oleh hukum Republik Indonesia.</p>

<h3>10. Kontak</h3>
<p>Untuk pertanyaan tentang Ketentuan ini, hubungi: <a href="mailto:legal@youtubeautomation.com">legal@youtubeautomation.com</a></p>
"""


# ============================================================================
# TERMS OF SERVICE CONTENT - VERSION 2.0.0 (Active)
# ============================================================================

TERMS_OF_SERVICE_CONTENT_V2 = """
# Syarat dan Ketentuan Layanan
## YouTube Automation Platform

**Versi 2.0 - Berlaku sejak: 1 Januari 2025**

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
- Monitoring strike dan copyright

### 3. Akun Pengguna

3.1. Anda harus berusia minimal 18 tahun untuk menggunakan Platform.
3.2. Anda bertanggung jawab menjaga kerahasiaan kredensial akun Anda.
3.3. Anda bertanggung jawab atas semua aktivitas yang terjadi di akun Anda.
3.4. Satu akun hanya boleh digunakan oleh satu individu atau entitas.
3.5. Anda wajib menggunakan autentikasi dua faktor (2FA) untuk keamanan akun.

### 4. Koneksi Akun YouTube

4.1. Dengan menghubungkan akun YouTube Anda, Anda memberikan izin kepada Platform untuk mengakses dan mengelola channel sesuai dengan permission yang diberikan.
4.2. Platform tidak bertanggung jawab atas tindakan YouTube terhadap channel Anda.
4.3. Anda dapat mencabut akses kapan saja melalui pengaturan akun Google Anda.

### 5. Penggunaan yang Dilarang

Anda dilarang menggunakan Platform untuk:
- Melanggar Ketentuan Layanan YouTube atau platform streaming lainnya
- Menyebarkan konten ilegal, berbahaya, atau menyesatkan
- Spam atau aktivitas yang mengganggu
- Mengakses sistem tanpa izin
- Menjual kembali layanan tanpa izin tertulis
- Menggunakan bot atau script otomatis di luar fitur Platform
- Melakukan aktivitas yang dapat menyebabkan strike pada channel

### 6. Pembayaran dan Langganan

6.1. Biaya langganan ditagih sesuai paket yang dipilih (bulanan atau tahunan).
6.2. Pembayaran tahunan mendapat diskon hingga 17%.
6.3. Pembayaran tidak dapat dikembalikan kecuali dalam 30 hari pertama.
6.4. Kami berhak mengubah harga dengan pemberitahuan 30 hari sebelumnya.
6.5. Kegagalan pembayaran dapat mengakibatkan penangguhan layanan.
6.6. Kami menerima pembayaran melalui berbagai metode termasuk kartu kredit, e-wallet, dan transfer bank.

### 7. Privasi Data dan GDPR

7.1. Penggunaan data Anda diatur oleh Kebijakan Privasi kami.
7.2. Anda berhak meminta ekspor data pribadi Anda kapan saja.
7.3. Anda berhak meminta penghapusan akun dan data Anda.
7.4. Kami memproses data sesuai dengan GDPR dan regulasi privasi yang berlaku.
7.5. Data Anda dienkripsi dan disimpan dengan aman di server yang berlokasi di Indonesia.

### 8. Keamanan

8.1. Kami menerapkan enkripsi end-to-end untuk data sensitif.
8.2. Autentikasi dua faktor (2FA) tersedia dan sangat direkomendasikan.
8.3. Kami melakukan audit keamanan secara berkala.
8.4. Kami akan memberitahu Anda dalam 72 jam jika terjadi pelanggaran data yang mempengaruhi akun Anda.

### 9. Batasan Tanggung Jawab

Platform disediakan "sebagaimana adanya" tanpa jaminan apapun. Kami tidak bertanggung jawab atas:
- Kerugian tidak langsung yang timbul dari penggunaan Platform
- Tindakan YouTube atau platform pihak ketiga terhadap akun Anda
- Downtime yang disebabkan oleh pemeliharaan terjadwal
- Kehilangan data akibat kelalaian pengguna
- Strike atau penalti yang diterima channel Anda dari YouTube

### 10. Penghentian Layanan

10.1. Anda dapat membatalkan langganan kapan saja melalui dashboard.
10.2. Kami dapat menangguhkan atau menghentikan akun yang melanggar Ketentuan ini.
10.3. Data akan disimpan selama 30 hari setelah penghentian akun.
10.4. Anda dapat meminta ekspor data sebelum penghapusan akun.

### 11. Perubahan Ketentuan

Kami dapat mengubah Ketentuan ini kapan saja. Perubahan material akan diberitahukan melalui email atau notifikasi di Platform minimal 14 hari sebelum berlaku. Penggunaan berkelanjutan setelah perubahan berarti Anda menerima ketentuan baru.

### 12. Hukum yang Berlaku

Ketentuan ini diatur oleh hukum Republik Indonesia. Sengketa akan diselesaikan melalui arbitrase di Jakarta sesuai dengan aturan Badan Arbitrase Nasional Indonesia (BANI).

### 13. Kontak

Untuk pertanyaan tentang Ketentuan ini, hubungi:
- Email: legal@youtubeautomation.com
- Support: support@youtubeautomation.com
- Alamat: Jakarta, Indonesia
"""


TERMS_OF_SERVICE_HTML_V2 = """
<h1>Syarat dan Ketentuan Layanan</h1>
<h2>YouTube Automation Platform</h2>

<p><strong>Versi 2.0 - Berlaku sejak: 1 Januari 2025</strong></p>

<h3>1. Penerimaan Ketentuan</h3>
<p>Dengan mengakses atau menggunakan YouTube Automation Platform ("Platform"), Anda setuju untuk terikat oleh Syarat dan Ketentuan ini. Jika Anda tidak setuju dengan ketentuan ini, mohon untuk tidak menggunakan Platform.</p>

<h3>2. Deskripsi Layanan</h3>
<p>Platform menyediakan layanan otomatisasi YouTube termasuk:</p>
<ul>
    <li>Manajemen multi-akun YouTube</li>
    <li>Penjadwalan upload video otomatis</li>
    <li>Live streaming otomatis dengan playlist</li>
    <li>Generasi thumbnail menggunakan AI</li>
    <li>Generasi judul dan deskripsi menggunakan AI</li>
    <li>Analitik dan pelaporan performa</li>
    <li>Moderasi chat otomatis</li>
    <li>Integrasi multi-platform streaming</li>
    <li>Monitoring strike dan copyright</li>
</ul>

<h3>3. Akun Pengguna</h3>
<p>3.1. Anda harus berusia minimal 18 tahun untuk menggunakan Platform.</p>
<p>3.2. Anda bertanggung jawab menjaga kerahasiaan kredensial akun Anda.</p>
<p>3.3. Anda bertanggung jawab atas semua aktivitas yang terjadi di akun Anda.</p>
<p>3.4. Satu akun hanya boleh digunakan oleh satu individu atau entitas.</p>
<p>3.5. Anda wajib menggunakan autentikasi dua faktor (2FA) untuk keamanan akun.</p>

<h3>4. Koneksi Akun YouTube</h3>
<p>4.1. Dengan menghubungkan akun YouTube Anda, Anda memberikan izin kepada Platform untuk mengakses dan mengelola channel sesuai dengan permission yang diberikan.</p>
<p>4.2. Platform tidak bertanggung jawab atas tindakan YouTube terhadap channel Anda.</p>
<p>4.3. Anda dapat mencabut akses kapan saja melalui pengaturan akun Google Anda.</p>

<h3>5. Penggunaan yang Dilarang</h3>
<p>Anda dilarang menggunakan Platform untuk:</p>
<ul>
    <li>Melanggar Ketentuan Layanan YouTube atau platform streaming lainnya</li>
    <li>Menyebarkan konten ilegal, berbahaya, atau menyesatkan</li>
    <li>Spam atau aktivitas yang mengganggu</li>
    <li>Mengakses sistem tanpa izin</li>
    <li>Menjual kembali layanan tanpa izin tertulis</li>
    <li>Menggunakan bot atau script otomatis di luar fitur Platform</li>
    <li>Melakukan aktivitas yang dapat menyebabkan strike pada channel</li>
</ul>

<h3>6. Pembayaran dan Langganan</h3>
<p>6.1. Biaya langganan ditagih sesuai paket yang dipilih (bulanan atau tahunan).</p>
<p>6.2. Pembayaran tahunan mendapat diskon hingga 17%.</p>
<p>6.3. Pembayaran tidak dapat dikembalikan kecuali dalam 30 hari pertama.</p>
<p>6.4. Kami berhak mengubah harga dengan pemberitahuan 30 hari sebelumnya.</p>
<p>6.5. Kegagalan pembayaran dapat mengakibatkan penangguhan layanan.</p>
<p>6.6. Kami menerima pembayaran melalui berbagai metode termasuk kartu kredit, e-wallet, dan transfer bank.</p>

<h3>7. Privasi Data dan GDPR</h3>
<p>7.1. Penggunaan data Anda diatur oleh Kebijakan Privasi kami.</p>
<p>7.2. Anda berhak meminta ekspor data pribadi Anda kapan saja.</p>
<p>7.3. Anda berhak meminta penghapusan akun dan data Anda.</p>
<p>7.4. Kami memproses data sesuai dengan GDPR dan regulasi privasi yang berlaku.</p>
<p>7.5. Data Anda dienkripsi dan disimpan dengan aman di server yang berlokasi di Indonesia.</p>

<h3>8. Keamanan</h3>
<p>8.1. Kami menerapkan enkripsi end-to-end untuk data sensitif.</p>
<p>8.2. Autentikasi dua faktor (2FA) tersedia dan sangat direkomendasikan.</p>
<p>8.3. Kami melakukan audit keamanan secara berkala.</p>
<p>8.4. Kami akan memberitahu Anda dalam 72 jam jika terjadi pelanggaran data yang mempengaruhi akun Anda.</p>

<h3>9. Batasan Tanggung Jawab</h3>
<p>Platform disediakan "sebagaimana adanya" tanpa jaminan apapun. Kami tidak bertanggung jawab atas:</p>
<ul>
    <li>Kerugian tidak langsung yang timbul dari penggunaan Platform</li>
    <li>Tindakan YouTube atau platform pihak ketiga terhadap akun Anda</li>
    <li>Downtime yang disebabkan oleh pemeliharaan terjadwal</li>
    <li>Kehilangan data akibat kelalaian pengguna</li>
    <li>Strike atau penalti yang diterima channel Anda dari YouTube</li>
</ul>

<h3>10. Penghentian Layanan</h3>
<p>10.1. Anda dapat membatalkan langganan kapan saja melalui dashboard.</p>
<p>10.2. Kami dapat menangguhkan atau menghentikan akun yang melanggar Ketentuan ini.</p>
<p>10.3. Data akan disimpan selama 30 hari setelah penghentian akun.</p>
<p>10.4. Anda dapat meminta ekspor data sebelum penghapusan akun.</p>

<h3>11. Perubahan Ketentuan</h3>
<p>Kami dapat mengubah Ketentuan ini kapan saja. Perubahan material akan diberitahukan melalui email atau notifikasi di Platform minimal 14 hari sebelum berlaku. Penggunaan berkelanjutan setelah perubahan berarti Anda menerima ketentuan baru.</p>

<h3>12. Hukum yang Berlaku</h3>
<p>Ketentuan ini diatur oleh hukum Republik Indonesia. Sengketa akan diselesaikan melalui arbitrase di Jakarta sesuai dengan aturan Badan Arbitrase Nasional Indonesia (BANI).</p>

<h3>13. Kontak</h3>
<p>Untuk pertanyaan tentang Ketentuan ini, hubungi:</p>
<ul>
    <li>Email: <a href="mailto:legal@youtubeautomation.com">legal@youtubeautomation.com</a></li>
    <li>Support: <a href="mailto:support@youtubeautomation.com">support@youtubeautomation.com</a></li>
    <li>Alamat: Jakarta, Indonesia</li>
</ul>
"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_system_user_id(session) -> uuid.UUID:
    """Get a user ID for seeding. Tries admin first, then any user."""
    # Try to get admin user first
    admin_result = await session.execute(select(Admin).limit(1))
    admin = admin_result.scalar_one_or_none()
    if admin:
        print(f"   Using admin user: {admin.user_id}")
        return admin.user_id
    
    # Try to get any user
    user_result = await session.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    if user:
        print(f"   Using regular user: {user.id}")
        return user.id
    
    # No users exist - this shouldn't happen in normal usage
    raise Exception("No users found in database. Please create a user first.")


# ============================================================================
# SEED FUNCTIONS
# ============================================================================

async def seed_terms_of_service():
    """Seed sample Terms of Service versions."""
    async with async_session_maker() as session:
        # Check if ToS already exist
        result = await session.execute(select(TermsOfService).limit(1))
        if result.scalar_one_or_none():
            print("⏭️  Terms of Service already exist. Skipping seed.")
            return 0

        # Get user ID for created_by field
        try:
            user_id = await get_system_user_id(session)
        except Exception as e:
            print(f"❌ Error: {e}")
            return 0

        now = datetime.utcnow()

        terms_versions = [
            TermsOfService(
                version="1.0.0",
                title="Syarat dan Ketentuan Layanan",
                content=TERMS_OF_SERVICE_CONTENT_V1.strip(),
                content_html=TERMS_OF_SERVICE_HTML_V1.strip(),
                summary="Versi awal Terms of Service untuk YouTube Automation Platform",
                status=TermsOfServiceStatus.ARCHIVED.value,
                effective_date=now - timedelta(days=90),
                created_by=user_id,
                activated_by=user_id,
                activated_at=now - timedelta(days=90),
            ),
            TermsOfService(
                version="2.0.0",
                title="Syarat dan Ketentuan Layanan",
                content=TERMS_OF_SERVICE_CONTENT_V2.strip(),
                content_html=TERMS_OF_SERVICE_HTML_V2.strip(),
                summary="Update: Penambahan ketentuan GDPR, keamanan, koneksi YouTube, dan fitur baru AI",
                status=TermsOfServiceStatus.ACTIVE.value,
                effective_date=now - timedelta(days=5),
                created_by=user_id,
                activated_by=user_id,
                activated_at=now - timedelta(days=5),
            ),
        ]

        for terms in terms_versions:
            session.add(terms)

        await session.commit()
        print(f"✅ Successfully seeded {len(terms_versions)} Terms of Service versions:")
        print(f"   - v1.0.0 (Archived)")
        print(f"   - v2.0.0 (Active)")
        return len(terms_versions)


async def seed_compliance_reports():
    """Seed sample Compliance Reports."""
    async with async_session_maker() as session:
        # Check if reports already exist
        result = await session.execute(select(ComplianceReport).limit(1))
        if result.scalar_one_or_none():
            print("⏭️  Compliance Reports already exist. Skipping seed.")
            return 0

        # Get user ID for requested_by field
        try:
            user_id = await get_system_user_id(session)
        except Exception as e:
            print(f"❌ Error: {e}")
            return 0

        now = datetime.utcnow()

        reports = [
            ComplianceReport(
                report_type=ComplianceReportType.GDPR_COMPLIANCE.value,
                title="GDPR Compliance Report Q4 2024",
                description="Laporan kepatuhan GDPR untuk kuartal 4 tahun 2024",
                status=ComplianceReportStatus.COMPLETED.value,
                start_date=now - timedelta(days=120),
                end_date=now - timedelta(days=30),
                parameters={"include_user_data": True, "include_consent_logs": True},
                file_path="/reports/gdpr_q4_2024.pdf",
                file_size=1024 * 512,
                error_message=None,
                requested_by=user_id,
                completed_at=now - timedelta(days=25),
            ),
            ComplianceReport(
                report_type=ComplianceReportType.SECURITY_AUDIT.value,
                title="Security Audit Report December 2024",
                description="Audit keamanan sistem bulanan",
                status=ComplianceReportStatus.COMPLETED.value,
                start_date=now - timedelta(days=60),
                end_date=now - timedelta(days=30),
                parameters={"include_vulnerability_scan": True, "include_access_logs": True},
                file_path="/reports/security_audit_dec_2024.pdf",
                file_size=1024 * 256,
                error_message=None,
                requested_by=user_id,
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
                file_size=1024 * 1024,
                error_message=None,
                requested_by=user_id,
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
                requested_by=user_id,
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
                requested_by=user_id,
            ),
        ]

        for report in reports:
            session.add(report)

        await session.commit()
        print(f"✅ Successfully seeded {len(reports)} Compliance Reports.")
        return len(reports)


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run all compliance seed functions."""
    print("=" * 60)
    print("🌱 SEEDING COMPLIANCE DATA")
    print("=" * 60)
    
    print("\n📋 Terms of Service:")
    tos_count = await seed_terms_of_service()
    
    print("\n📊 Compliance Reports:")
    reports_count = await seed_compliance_reports()
    
    print("\n" + "=" * 60)
    print("✨ SEEDING COMPLETE!")
    print(f"   - Terms of Service: {tos_count} versions")
    print(f"   - Compliance Reports: {reports_count} reports")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
