"""Script to create default Terms of Service.

Run with: python -m scripts.create_default_tos
"""

import asyncio
import uuid
from datetime import datetime

from sqlalchemy import select
from app.core.database import async_session_maker
from app.modules.admin.models import Admin, TermsOfService, TermsOfServiceStatus


DEFAULT_TOS_CONTENT = """
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

DEFAULT_TOS_HTML = """
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


async def create_default_tos():
    """Create default Terms of Service if none exists."""
    async with async_session_maker() as session:
        # Check if active ToS exists
        result = await session.execute(
            select(TermsOfService).where(
                TermsOfService.status == TermsOfServiceStatus.ACTIVE.value
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"✅ Active Terms of Service already exists: v{existing.version}")
            return
        
        # Get admin user_id from admins table
        admin_result = await session.execute(select(Admin).limit(1))
        admin = admin_result.scalar_one_or_none()
        
        if not admin:
            print("❌ Error: No admin found in database. Please create an admin first.")
            return
        
        admin_user_id = admin.user_id
        print(f"📋 Using admin user_id: {admin_user_id}")
        
        # Create new ToS
        tos = TermsOfService(
            id=uuid.uuid4(),
            version="2.0.0",
            title="Syarat dan Ketentuan Layanan",
            content=DEFAULT_TOS_CONTENT.strip(),
            content_html=DEFAULT_TOS_HTML.strip(),
            summary="Syarat dan Ketentuan Layanan YouTube Automation Platform - mencakup penggunaan layanan, pembayaran, privasi data, dan keamanan.",
            status=TermsOfServiceStatus.ACTIVE.value,
            effective_date=datetime.utcnow(),
            created_by=admin_user_id,
            activated_by=admin_user_id,
            activated_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        session.add(tos)
        await session.commit()
        
        print(f"✅ Created Terms of Service v{tos.version}")
        print(f"   ID: {tos.id}")
        print(f"   Status: ACTIVE")
        print(f"   Title: {tos.title}")


if __name__ == "__main__":
    asyncio.run(create_default_tos())
