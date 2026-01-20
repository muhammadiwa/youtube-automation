"use client"

import { useState } from "react"
import Link from "next/link"
import {
    Webhook,
    Shield,
    RefreshCw,
    Check,
    Copy,
    ChevronRight,
    AlertTriangle,
    Clock,
    Zap,
    Code,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const webhookEvents = [
    { event: "video.uploaded", description: "Video berhasil diupload ke library", category: "Videos" },
    { event: "video.published", description: "Video dipublikasikan ke YouTube", category: "Videos" },
    { event: "video.deleted", description: "Video dihapus dari sistem", category: "Videos" },
    { event: "video.metadata_updated", description: "Metadata video diupdate", category: "Videos" },
    { event: "stream.started", description: "Live streaming dimulai", category: "Streams" },
    { event: "stream.ended", description: "Live streaming berakhir", category: "Streams" },
    { event: "stream.health_changed", description: "Status kesehatan stream berubah", category: "Streams" },
    { event: "account.connected", description: "Akun YouTube terhubung", category: "Accounts" },
    { event: "account.disconnected", description: "Akun YouTube terputus", category: "Accounts" },
    { event: "account.token_expired", description: "Token akun expired", category: "Accounts" },
    { event: "comment.received", description: "Komentar baru diterima", category: "Comments" },
    { event: "comment.replied", description: "Balasan komentar terkirim", category: "Comments" },
    { event: "analytics.updated", description: "Data analytics diupdate", category: "Analytics" },
    { event: "revenue.updated", description: "Data revenue diupdate", category: "Analytics" },
    { event: "job.completed", description: "Background job selesai", category: "Jobs" },
    { event: "job.failed", description: "Background job gagal", category: "Jobs" },
    { event: "payment.completed", description: "Pembayaran berhasil", category: "Billing" },
    { event: "payment.failed", description: "Pembayaran gagal", category: "Billing" },
]

const retrySchedule = [
    { attempt: 1, delay: "Immediate", total: "0s" },
    { attempt: 2, delay: "1 menit", total: "1m" },
    { attempt: 3, delay: "5 menit", total: "6m" },
    { attempt: 4, delay: "30 menit", total: "36m" },
    { attempt: 5, delay: "2 jam", total: "2h 36m" },
]

export default function WebhooksDocsPage() {
    const [copiedCode, setCopiedCode] = useState<string | null>(null)

    const copyToClipboard = async (code: string, id: string) => {
        await navigator.clipboard.writeText(code)
        setCopiedCode(id)
        setTimeout(() => setCopiedCode(null), 2000)
    }

    const CodeBlock = ({ code, language, id }: { code: string; language: string; id: string }) => (
        <div className="relative">
            <div className="flex items-center justify-between px-4 py-2 bg-slate-800 rounded-t-lg border-b border-slate-700">
                <span className="text-xs text-slate-400">{language}</span>
                <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-slate-400 hover:text-white"
                    onClick={() => copyToClipboard(code, id)}
                >
                    {copiedCode === id ? (
                        <Check className="h-3 w-3 text-green-500" />
                    ) : (
                        <Copy className="h-3 w-3" />
                    )}
                </Button>
            </div>
            <pre className="p-4 rounded-b-lg bg-slate-900 text-slate-100 text-sm overflow-x-auto">
                <code>{code}</code>
            </pre>
        </div>
    )

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Documentation", href: "/dashboard/docs" },
                { label: "Webhooks" },
            ]}
        >
            <div className="space-y-8 max-w-5xl">
                {/* Header */}
                <div>
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-green-500">
                            <Webhook className="h-6 w-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold">Webhooks</h1>
                            <p className="text-muted-foreground">
                                Terima notifikasi real-time saat event terjadi di platform
                            </p>
                        </div>
                    </div>
                </div>

                {/* Quick Navigation */}
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-lg">Daftar Isi</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid md:grid-cols-2 gap-2">
                            {[
                                { id: "overview", title: "Overview", icon: Zap },
                                { id: "create", title: "Membuat Webhook", icon: Webhook },
                                { id: "events", title: "Event Types", icon: Code },
                                { id: "payload", title: "Payload Format", icon: Code },
                                { id: "signature", title: "Signature Verification", icon: Shield },
                                { id: "retry", title: "Retry Policy", icon: RefreshCw },
                            ].map((item) => (
                                <a
                                    key={item.id}
                                    href={`#${item.id}`}
                                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted transition-colors"
                                >
                                    <item.icon className="h-4 w-4 text-muted-foreground" />
                                    <span className="text-sm">{item.title}</span>
                                    <ChevronRight className="h-3 w-3 ml-auto text-muted-foreground" />
                                </a>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Overview Section */}
                <section id="overview" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Zap className="h-5 w-5 text-green-500" />
                                <CardTitle>Overview</CardTitle>
                            </div>
                            <CardDescription>
                                Apa itu webhooks dan bagaimana cara kerjanya
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <p className="text-muted-foreground">
                                Webhooks memungkinkan aplikasi Anda menerima notifikasi HTTP POST secara real-time
                                saat event tertentu terjadi di platform kami. Ini lebih efisien daripada polling API secara berkala.
                            </p>

                            <div className="grid md:grid-cols-3 gap-4">
                                <div className="p-4 rounded-lg border">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Zap className="h-4 w-4 text-green-500" />
                                        <span className="font-medium">Real-time</span>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                        Terima notifikasi segera saat event terjadi
                                    </p>
                                </div>
                                <div className="p-4 rounded-lg border">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Shield className="h-4 w-4 text-green-500" />
                                        <span className="font-medium">Secure</span>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                        Signature verification untuk keamanan
                                    </p>
                                </div>
                                <div className="p-4 rounded-lg border">
                                    <div className="flex items-center gap-2 mb-2">
                                        <RefreshCw className="h-4 w-4 text-green-500" />
                                        <span className="font-medium">Reliable</span>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                        Auto-retry dengan exponential backoff
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </section>

                {/* Create Webhook Section */}
                <section id="create" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Webhook className="h-5 w-5 text-green-500" />
                                <CardTitle>Membuat Webhook</CardTitle>
                            </div>
                            <CardDescription>
                                Langkah-langkah membuat webhook endpoint
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div>
                                <h4 className="font-medium mb-3">Via Dashboard</h4>
                                <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                                    <li>Buka <Link href="/dashboard/settings/webhooks" className="text-primary hover:underline">Settings → Webhooks</Link></li>
                                    <li>Klik tombol "Add Webhook"</li>
                                    <li>Masukkan nama dan URL endpoint Anda</li>
                                    <li>Pilih events yang ingin diterima</li>
                                    <li>Simpan webhook secret untuk verifikasi signature</li>
                                </ol>
                            </div>

                            <div>
                                <h4 className="font-medium mb-3">Via API</h4>
                                <CodeBlock
                                    language="HTTP"
                                    id="create-webhook"
                                    code={`POST /api/v1/integration/webhooks HTTP/1.1
Host: ${new URL(API_BASE_URL).host}
X-API-Key: yt_live_abc123...
Content-Type: application/json

{
  "name": "My Webhook",
  "url": "https://your-server.com/webhook",
  "events": ["video.uploaded", "video.published", "stream.started"]
}`}
                                />
                            </div>

                            <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                                <div className="flex items-start gap-3">
                                    <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
                                    <div>
                                        <p className="font-medium text-amber-500">Penting</p>
                                        <p className="text-sm text-muted-foreground">
                                            Webhook secret hanya ditampilkan sekali saat pembuatan. Simpan dengan aman untuk verifikasi signature.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="flex gap-3">
                                <Link href="/dashboard/settings/webhooks">
                                    <Button>
                                        <Webhook className="h-4 w-4 mr-2" />
                                        Kelola Webhooks
                                    </Button>
                                </Link>
                            </div>
                        </CardContent>
                    </Card>
                </section>

                {/* Events Section */}
                <section id="events" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Code className="h-5 w-5 text-green-500" />
                                <CardTitle>Event Types</CardTitle>
                            </div>
                            <CardDescription>
                                Daftar event yang dapat di-subscribe
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Event</TableHead>
                                        <TableHead>Kategori</TableHead>
                                        <TableHead>Deskripsi</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {webhookEvents.map((event) => (
                                        <TableRow key={event.event}>
                                            <TableCell>
                                                <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">
                                                    {event.event}
                                                </code>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline">{event.category}</Badge>
                                            </TableCell>
                                            <TableCell className="text-muted-foreground">
                                                {event.description}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </section>

                {/* Payload Section */}
                <section id="payload" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Code className="h-5 w-5 text-green-500" />
                                <CardTitle>Payload Format</CardTitle>
                            </div>
                            <CardDescription>
                                Format data yang dikirim ke webhook endpoint
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div>
                                <h4 className="font-medium mb-3">Request Headers</h4>
                                <CodeBlock
                                    language="HTTP"
                                    id="webhook-headers"
                                    code={`POST /your-webhook-endpoint HTTP/1.1
Content-Type: application/json
X-Webhook-Signature: t=1705312200,v1=5257a869e7ecebeda32affa62cdca3fa51cad7e77a0e56ff536d0ce8e108d8bd
X-Webhook-Event: video.uploaded
X-Webhook-Delivery-Id: del_abc123`}
                                />
                            </div>

                            <div>
                                <h4 className="font-medium mb-3">Request Body</h4>
                                <CodeBlock
                                    language="JSON"
                                    id="webhook-payload"
                                    code={`{
  "event_id": "evt_abc123xyz",
  "event_type": "video.uploaded",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "video_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "My Awesome Video",
    "status": "uploaded",
    "account_id": "660e8400-e29b-41d4-a716-446655440001",
    "file_size": 104857600,
    "duration": 300
  }
}`}
                                />
                            </div>
                        </CardContent>
                    </Card>
                </section>

                {/* Signature Verification Section */}
                <section id="signature" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Shield className="h-5 w-5 text-green-500" />
                                <CardTitle>Signature Verification</CardTitle>
                            </div>
                            <CardDescription>
                                Cara memverifikasi keaslian webhook request
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
                                <div className="flex items-start gap-3">
                                    <Shield className="h-5 w-5 text-blue-500 mt-0.5" />
                                    <div>
                                        <p className="font-medium text-blue-500">Mengapa Verifikasi Penting?</p>
                                        <p className="text-sm text-muted-foreground">
                                            Verifikasi signature memastikan bahwa webhook request benar-benar berasal dari server kami
                                            dan tidak dimodifikasi selama transit.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h4 className="font-medium mb-3">Signature Header Format</h4>
                                <CodeBlock
                                    language="Text"
                                    id="sig-format"
                                    code={`X-Webhook-Signature: t=1705312200,v1=5257a869e7ecebeda32affa62cdca3fa51cad7e77a0e56ff536d0ce8e108d8bd`}
                                />
                                <p className="text-sm text-muted-foreground mt-2">
                                    <code className="px-1 bg-muted rounded">t</code> = Unix timestamp saat signature dibuat<br />
                                    <code className="px-1 bg-muted rounded">v1</code> = HMAC-SHA256 signature
                                </p>
                            </div>

                            <div>
                                <h4 className="font-medium mb-3">Implementasi Verifikasi</h4>
                                <Tabs defaultValue="python">
                                    <TabsList>
                                        <TabsTrigger value="python">Python</TabsTrigger>
                                        <TabsTrigger value="javascript">Node.js</TabsTrigger>
                                        <TabsTrigger value="php">PHP</TabsTrigger>
                                    </TabsList>
                                    <TabsContent value="python" className="mt-4">
                                        <CodeBlock
                                            language="Python"
                                            id="verify-python"
                                            code={`import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    """Verifikasi webhook signature."""
    # Parse signature header
    parts = dict(item.split("=") for item in signature_header.split(","))
    timestamp = parts.get("t")
    signature = parts.get("v1")
    
    if not timestamp or not signature:
        return False
    
    # Buat signed payload
    signed_payload = f"{timestamp}.{payload.decode()}"
    
    # Hitung expected signature
    expected = hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)

# Penggunaan di Flask/FastAPI
@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-Webhook-Signature")
    
    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = json.loads(payload)
    # Process webhook...`}
                                        />
                                    </TabsContent>
                                    <TabsContent value="javascript" className="mt-4">
                                        <CodeBlock
                                            language="JavaScript"
                                            id="verify-js"
                                            code={`const crypto = require('crypto');

function verifyWebhookSignature(payload, signatureHeader, secret) {
  const parts = Object.fromEntries(
    signatureHeader.split(',').map(item => item.split('='))
  );
  
  const timestamp = parts.t;
  const signature = parts.v1;
  
  if (!timestamp || !signature) return false;
  
  const signedPayload = \`\${timestamp}.\${payload}\`;
  const expected = crypto
    .createHmac('sha256', secret)
    .update(signedPayload)
    .digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

// Express middleware
app.post('/webhook', express.raw({type: 'application/json'}), (req, res) => {
  const signature = req.headers['x-webhook-signature'];
  
  if (!verifyWebhookSignature(req.body.toString(), signature, WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid signature');
  }
  
  const data = JSON.parse(req.body);
  // Process webhook...
});`}
                                        />
                                    </TabsContent>
                                    <TabsContent value="php" className="mt-4">
                                        <CodeBlock
                                            language="PHP"
                                            id="verify-php"
                                            code={`<?php
function verifyWebhookSignature($payload, $signatureHeader, $secret) {
    $parts = [];
    foreach (explode(',', $signatureHeader) as $item) {
        list($key, $value) = explode('=', $item, 2);
        $parts[$key] = $value;
    }
    
    $timestamp = $parts['t'] ?? null;
    $signature = $parts['v1'] ?? null;
    
    if (!$timestamp || !$signature) {
        return false;
    }
    
    $signedPayload = $timestamp . '.' . $payload;
    $expected = hash_hmac('sha256', $signedPayload, $secret);
    
    return hash_equals($signature, $expected);
}

// Penggunaan
$payload = file_get_contents('php://input');
$signature = $_SERVER['HTTP_X_WEBHOOK_SIGNATURE'] ?? '';

if (!verifyWebhookSignature($payload, $signature, WEBHOOK_SECRET)) {
    http_response_code(401);
    exit('Invalid signature');
}

$data = json_decode($payload, true);
// Process webhook...`}
                                        />
                                    </TabsContent>
                                </Tabs>
                            </div>
                        </CardContent>
                    </Card>
                </section>

                {/* Retry Policy Section */}
                <section id="retry" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <RefreshCw className="h-5 w-5 text-green-500" />
                                <CardTitle>Retry Policy</CardTitle>
                            </div>
                            <CardDescription>
                                Kebijakan retry jika webhook delivery gagal
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <p className="text-muted-foreground">
                                Jika webhook delivery gagal (non-2xx response atau timeout), sistem akan otomatis
                                melakukan retry dengan exponential backoff.
                            </p>

                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Attempt</TableHead>
                                        <TableHead>Delay</TableHead>
                                        <TableHead>Total Time</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {retrySchedule.map((item) => (
                                        <TableRow key={item.attempt}>
                                            <TableCell className="font-medium">#{item.attempt}</TableCell>
                                            <TableCell>{item.delay}</TableCell>
                                            <TableCell className="text-muted-foreground">{item.total}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>

                            <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                                <div className="flex items-start gap-3">
                                    <Clock className="h-5 w-5 text-amber-500 mt-0.5" />
                                    <div>
                                        <p className="font-medium text-amber-500">Timeout</p>
                                        <p className="text-sm text-muted-foreground">
                                            Webhook endpoint harus merespons dalam 30 detik. Jika tidak, request dianggap gagal dan akan di-retry.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h4 className="font-medium mb-3">Best Practices</h4>
                                <ul className="space-y-2 text-sm text-muted-foreground">
                                    <li className="flex items-start gap-2">
                                        <Check className="h-4 w-4 text-green-500 mt-0.5" />
                                        <span><strong>Respond cepat</strong> - Return 2xx dalam 30 detik, process di background</span>
                                    </li>
                                    <li className="flex items-start gap-2">
                                        <Check className="h-4 w-4 text-green-500 mt-0.5" />
                                        <span><strong>Idempotency</strong> - Handle duplicate events dengan menyimpan event_id</span>
                                    </li>
                                    <li className="flex items-start gap-2">
                                        <Check className="h-4 w-4 text-green-500 mt-0.5" />
                                        <span><strong>Verifikasi signature</strong> - Selalu validasi signature sebelum processing</span>
                                    </li>
                                    <li className="flex items-start gap-2">
                                        <Check className="h-4 w-4 text-green-500 mt-0.5" />
                                        <span><strong>Queue processing</strong> - Gunakan message queue untuk reliability</span>
                                    </li>
                                </ul>
                            </div>
                        </CardContent>
                    </Card>
                </section>

                {/* Support */}
                <Card className="border-0 shadow-lg">
                    <CardContent className="p-6">
                        <div className="flex flex-col md:flex-row items-center gap-6">
                            <div className="p-4 rounded-2xl bg-gradient-to-br from-green-500/10 to-emerald-500/10">
                                <Webhook className="h-12 w-12 text-green-500" />
                            </div>
                            <div className="flex-1 text-center md:text-left">
                                <h3 className="text-xl font-bold mb-2">Siap Setup Webhook?</h3>
                                <p className="text-muted-foreground">
                                    Mulai terima notifikasi real-time untuk aplikasi Anda.
                                </p>
                            </div>
                            <div className="flex gap-3">
                                <Link href="/dashboard/settings/webhooks">
                                    <Button>
                                        <Webhook className="h-4 w-4 mr-2" />
                                        Setup Webhook
                                    </Button>
                                </Link>
                                <Link href="/dashboard/docs/api">
                                    <Button variant="outline">
                                        <Code className="h-4 w-4 mr-2" />
                                        API Docs
                                    </Button>
                                </Link>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    )
}
