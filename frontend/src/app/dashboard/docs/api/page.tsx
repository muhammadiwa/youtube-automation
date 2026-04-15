"use client"

import { useState } from "react"
import Link from "next/link"
import {
    Code,
    Key,
    Shield,
    Clock,
    AlertTriangle,
    Check,
    Copy,
    ChevronRight,
    ExternalLink,
    Zap,
    Lock,
    Globe,
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

const scopes = [
    { scope: "read:accounts", description: "Membaca data akun YouTube yang terhubung", category: "Accounts" },
    { scope: "write:accounts", description: "Mengelola koneksi akun YouTube", category: "Accounts" },
    { scope: "read:videos", description: "Membaca data video dan metadata", category: "Videos" },
    { scope: "write:videos", description: "Upload, edit, dan hapus video", category: "Videos" },
    { scope: "read:streams", description: "Membaca data streaming", category: "Streams" },
    { scope: "write:streams", description: "Memulai dan mengelola live streaming", category: "Streams" },
    { scope: "read:analytics", description: "Membaca data analytics dan statistik", category: "Analytics" },
    { scope: "read:comments", description: "Membaca komentar video", category: "Comments" },
    { scope: "write:comments", description: "Membalas dan moderasi komentar", category: "Comments" },
    { scope: "admin:accounts", description: "Akses admin untuk manajemen akun", category: "Admin" },
    { scope: "admin:webhooks", description: "Mengelola konfigurasi webhooks", category: "Admin" },
    { scope: "*", description: "Full access - semua permission", category: "Full Access" },
]

const endpoints = [
    { method: "GET", path: "/api/v1/videos", description: "List semua video", scopes: ["read:videos"] },
    { method: "POST", path: "/api/v1/videos", description: "Upload video baru", scopes: ["write:videos"] },
    { method: "GET", path: "/api/v1/videos/{id}", description: "Get detail video", scopes: ["read:videos"] },
    { method: "PATCH", path: "/api/v1/videos/{id}", description: "Update metadata video", scopes: ["write:videos"] },
    { method: "DELETE", path: "/api/v1/videos/{id}", description: "Hapus video", scopes: ["write:videos"] },
    { method: "GET", path: "/api/v1/accounts", description: "List akun YouTube", scopes: ["read:accounts"] },
    { method: "POST", path: "/api/v1/accounts/oauth/initiate", description: "Mulai OAuth flow", scopes: ["write:accounts"] },
    { method: "GET", path: "/api/v1/streams", description: "List streaming", scopes: ["read:streams"] },
    { method: "POST", path: "/api/v1/streams", description: "Buat streaming baru", scopes: ["write:streams"] },
    { method: "GET", path: "/api/v1/analytics", description: "Get analytics data", scopes: ["read:analytics"] },
]

const errorCodes = [
    { code: 400, name: "Bad Request", description: "Request tidak valid atau parameter salah" },
    { code: 401, name: "Unauthorized", description: "API key tidak valid atau tidak ada" },
    { code: 403, name: "Forbidden", description: "Scope tidak mencukupi atau IP tidak diizinkan" },
    { code: 404, name: "Not Found", description: "Resource tidak ditemukan" },
    { code: 429, name: "Too Many Requests", description: "Rate limit terlampaui" },
    { code: 500, name: "Internal Server Error", description: "Error server internal" },
]

export default function APIDocsPage() {
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
                { label: "API Integration" },
            ]}
        >
            <div className="space-y-8 max-w-5xl">
                {/* Header */}
                <div>
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-purple-500">
                            <Code className="h-6 w-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold">API Integration</h1>
                            <p className="text-muted-foreground">
                                Dokumentasi lengkap untuk mengintegrasikan aplikasi Anda dengan API kami
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
                                { id: "auth", title: "Authentication", icon: Lock },
                                { id: "api-keys", title: "API Keys", icon: Key },
                                { id: "scopes", title: "Scopes & Permissions", icon: Shield },
                                { id: "endpoints", title: "Endpoints Reference", icon: Globe },
                                { id: "rate-limit", title: "Rate Limiting", icon: Clock },
                                { id: "errors", title: "Error Handling", icon: AlertTriangle },
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

                {/* Authentication Section */}
                <section id="auth" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Lock className="h-5 w-5 text-purple-500" />
                                <CardTitle>Authentication</CardTitle>
                            </div>
                            <CardDescription>
                                Cara mengautentikasi request ke API
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div>
                                <h4 className="font-medium mb-3">API Key Authentication</h4>
                                <p className="text-sm text-muted-foreground mb-4">
                                    Gunakan header <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">X-API-Key</code> untuk autentikasi:
                                </p>
                                <CodeBlock
                                    language="HTTP"
                                    id="auth-header"
                                    code={`GET /api/v1/videos HTTP/1.1
Host: ${new URL(API_BASE_URL).host}
X-API-Key: yt_live_abc123xyz789...`}
                                />
                            </div>

                            <div>
                                <h4 className="font-medium mb-3">JWT Authentication (Alternative)</h4>
                                <p className="text-sm text-muted-foreground mb-4">
                                    Untuk aplikasi web, gunakan JWT token dari login:
                                </p>
                                <CodeBlock
                                    language="HTTP"
                                    id="jwt-header"
                                    code={`GET /api/v1/videos HTTP/1.1
Host: ${new URL(API_BASE_URL).host}
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...`}
                                />
                            </div>

                            <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
                                <div className="flex items-start gap-3">
                                    <Zap className="h-5 w-5 text-blue-500 mt-0.5" />
                                    <div>
                                        <p className="font-medium text-blue-500">Rekomendasi</p>
                                        <p className="text-sm text-muted-foreground">
                                            Gunakan API Key untuk integrasi server-to-server dan JWT untuk aplikasi web client-side.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </section>

                {/* API Keys Section */}
                <section id="api-keys" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Key className="h-5 w-5 text-purple-500" />
                                <CardTitle>API Keys</CardTitle>
                            </div>
                            <CardDescription>
                                Membuat dan mengelola API keys
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div>
                                <h4 className="font-medium mb-3">Membuat API Key</h4>
                                <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground mb-4">
                                    <li>Buka <Link href="/dashboard/settings/api-keys" className="text-primary hover:underline">Settings → API Keys</Link></li>
                                    <li>Klik tombol "Create API Key"</li>
                                    <li>Masukkan nama dan pilih scopes yang diperlukan</li>
                                    <li>Simpan API key dengan aman (hanya ditampilkan sekali!)</li>
                                </ol>

                                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                                    <div className="flex items-start gap-3">
                                        <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
                                        <div>
                                            <p className="font-medium text-amber-500">Penting</p>
                                            <p className="text-sm text-muted-foreground">
                                                API key hanya ditampilkan sekali saat pembuatan. Pastikan Anda menyimpannya dengan aman.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h4 className="font-medium mb-3">Format API Key</h4>
                                <p className="text-sm text-muted-foreground mb-2">
                                    API key memiliki format: <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">yt_live_[random_string]</code>
                                </p>
                                <p className="text-sm text-muted-foreground">
                                    Contoh: <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">yt_live_abc123xyz789def456</code>
                                </p>
                            </div>

                            <div>
                                <h4 className="font-medium mb-3">IP Restriction (Opsional)</h4>
                                <p className="text-sm text-muted-foreground mb-4">
                                    Batasi API key hanya bisa digunakan dari IP tertentu untuk keamanan tambahan:
                                </p>
                                <CodeBlock
                                    language="JSON"
                                    id="ip-restriction"
                                    code={`{
  "allowed_ips": [
    "192.168.1.100",
    "10.0.0.0/8",
    "2001:db8::/32"
  ]
}`}
                                />
                            </div>

                            <div className="flex gap-3">
                                <Link href="/dashboard/settings/api-keys">
                                    <Button>
                                        <Key className="h-4 w-4 mr-2" />
                                        Kelola API Keys
                                    </Button>
                                </Link>
                            </div>
                        </CardContent>
                    </Card>
                </section>

                {/* Scopes Section */}
                <section id="scopes" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Shield className="h-5 w-5 text-purple-500" />
                                <CardTitle>Scopes & Permissions</CardTitle>
                            </div>
                            <CardDescription>
                                Daftar scope yang tersedia untuk API key
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Scope</TableHead>
                                        <TableHead>Kategori</TableHead>
                                        <TableHead>Deskripsi</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {scopes.map((scope) => (
                                        <TableRow key={scope.scope}>
                                            <TableCell>
                                                <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">
                                                    {scope.scope}
                                                </code>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline">{scope.category}</Badge>
                                            </TableCell>
                                            <TableCell className="text-muted-foreground">
                                                {scope.description}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </section>

                {/* Endpoints Section */}
                <section id="endpoints" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Globe className="h-5 w-5 text-purple-500" />
                                <CardTitle>Endpoints Reference</CardTitle>
                            </div>
                            <CardDescription>
                                Daftar endpoint API yang tersedia
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-24">Method</TableHead>
                                        <TableHead>Endpoint</TableHead>
                                        <TableHead>Deskripsi</TableHead>
                                        <TableHead>Scopes</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {endpoints.map((endpoint, idx) => (
                                        <TableRow key={idx}>
                                            <TableCell>
                                                <Badge
                                                    variant={endpoint.method === "GET" ? "secondary" : endpoint.method === "POST" ? "default" : endpoint.method === "DELETE" ? "destructive" : "outline"}
                                                >
                                                    {endpoint.method}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <code className="text-xs font-mono">{endpoint.path}</code>
                                            </TableCell>
                                            <TableCell className="text-muted-foreground text-sm">
                                                {endpoint.description}
                                            </TableCell>
                                            <TableCell>
                                                {endpoint.scopes.map((s) => (
                                                    <Badge key={s} variant="outline" className="text-xs mr-1">
                                                        {s}
                                                    </Badge>
                                                ))}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>

                            <div className="flex gap-3">
                                <a href={`${API_BASE_URL}/docs`} target="_blank" rel="noopener noreferrer">
                                    <Button variant="outline">
                                        <ExternalLink className="h-4 w-4 mr-2" />
                                        Lihat Swagger UI
                                    </Button>
                                </a>
                            </div>
                        </CardContent>
                    </Card>
                </section>

                {/* Rate Limiting Section */}
                <section id="rate-limit" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Clock className="h-5 w-5 text-purple-500" />
                                <CardTitle>Rate Limiting</CardTitle>
                            </div>
                            <CardDescription>
                                Batasan request per API key
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div>
                                <h4 className="font-medium mb-3">Default Limits</h4>
                                <div className="grid md:grid-cols-3 gap-4">
                                    <div className="p-4 rounded-lg border">
                                        <p className="text-2xl font-bold">60</p>
                                        <p className="text-sm text-muted-foreground">requests / menit</p>
                                    </div>
                                    <div className="p-4 rounded-lg border">
                                        <p className="text-2xl font-bold">1,000</p>
                                        <p className="text-sm text-muted-foreground">requests / jam</p>
                                    </div>
                                    <div className="p-4 rounded-lg border">
                                        <p className="text-2xl font-bold">10,000</p>
                                        <p className="text-sm text-muted-foreground">requests / hari</p>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h4 className="font-medium mb-3">Rate Limit Headers</h4>
                                <p className="text-sm text-muted-foreground mb-4">
                                    Setiap response menyertakan header rate limit:
                                </p>
                                <CodeBlock
                                    language="HTTP"
                                    id="rate-headers"
                                    code={`X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705312260`}
                                />
                            </div>

                            <div>
                                <h4 className="font-medium mb-3">Handling Rate Limits</h4>
                                <p className="text-sm text-muted-foreground mb-4">
                                    Jika melebihi limit, API mengembalikan <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">429 Too Many Requests</code>:
                                </p>
                                <CodeBlock
                                    language="JSON"
                                    id="rate-error"
                                    code={`{
  "detail": "Rate limit exceeded",
  "retry_after": 45
}`}
                                />
                            </div>
                        </CardContent>
                    </Card>
                </section>

                {/* Error Handling Section */}
                <section id="errors" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <AlertTriangle className="h-5 w-5 text-purple-500" />
                                <CardTitle>Error Handling</CardTitle>
                            </div>
                            <CardDescription>
                                HTTP status codes dan error responses
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-24">Code</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Deskripsi</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {errorCodes.map((error) => (
                                        <TableRow key={error.code}>
                                            <TableCell>
                                                <Badge variant={error.code >= 500 ? "destructive" : error.code >= 400 ? "secondary" : "default"}>
                                                    {error.code}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="font-medium">{error.name}</TableCell>
                                            <TableCell className="text-muted-foreground">{error.description}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>

                            <div>
                                <h4 className="font-medium mb-3">Error Response Format</h4>
                                <CodeBlock
                                    language="JSON"
                                    id="error-format"
                                    code={`{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "errors": [
    {
      "field": "title",
      "message": "Title is required"
    }
  ]
}`}
                                />
                            </div>
                        </CardContent>
                    </Card>
                </section>

                {/* Code Examples */}
                <section id="examples" className="scroll-mt-20">
                    <Card>
                        <CardHeader>
                            <CardTitle>Code Examples</CardTitle>
                            <CardDescription>
                                Contoh implementasi dalam berbagai bahasa
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Tabs defaultValue="python">
                                <TabsList>
                                    <TabsTrigger value="python">Python</TabsTrigger>
                                    <TabsTrigger value="javascript">JavaScript</TabsTrigger>
                                    <TabsTrigger value="php">PHP</TabsTrigger>
                                    <TabsTrigger value="curl">cURL</TabsTrigger>
                                </TabsList>
                                <TabsContent value="python" className="mt-4">
                                    <CodeBlock
                                        language="Python"
                                        id="python-example"
                                        code={`import requests

API_KEY = "yt_live_abc123..."
BASE_URL = "${API_BASE_URL}"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Get videos
response = requests.get(f"{BASE_URL}/videos", headers=headers)
videos = response.json()

# Upload video
files = {"file": open("video.mp4", "rb")}
data = {
    "account_id": "uuid",
    "title": "My Video",
    "visibility": "private"
}
response = requests.post(
    f"{BASE_URL}/videos",
    headers={"X-API-Key": API_KEY},
    files=files,
    data=data
)`}
                                    />
                                </TabsContent>
                                <TabsContent value="javascript" className="mt-4">
                                    <CodeBlock
                                        language="JavaScript"
                                        id="js-example"
                                        code={`const axios = require('axios');

const apiClient = axios.create({
  baseURL: '${API_BASE_URL}',
  headers: {
    'X-API-Key': 'yt_live_abc123...',
    'Content-Type': 'application/json'
  }
});

// Get videos
const { data: videos } = await apiClient.get('/videos');

// Create stream
const { data: stream } = await apiClient.post('/streams', {
  account_id: 'uuid',
  title: 'My Live Stream'
});`}
                                    />
                                </TabsContent>
                                <TabsContent value="php" className="mt-4">
                                    <CodeBlock
                                        language="PHP"
                                        id="php-example"
                                        code={`<?php
use GuzzleHttp\\Client;

$client = new Client([
    'base_uri' => '${API_BASE_URL}/',
    'headers' => [
        'X-API-Key' => 'yt_live_abc123...',
        'Content-Type' => 'application/json'
    ]
]);

// Get videos
$response = $client->get('videos');
$videos = json_decode($response->getBody(), true);

// Update video
$response = $client->patch('videos/uuid', [
    'json' => [
        'title' => 'Updated Title'
    ]
]);`}
                                    />
                                </TabsContent>
                                <TabsContent value="curl" className="mt-4">
                                    <CodeBlock
                                        language="Bash"
                                        id="curl-example"
                                        code={`# Get videos
curl -X GET "${API_BASE_URL}/videos" \\
  -H "X-API-Key: yt_live_abc123..."

# Create webhook
curl -X POST "${API_BASE_URL}/integration/webhooks" \\
  -H "X-API-Key: yt_live_abc123..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "My Webhook",
    "url": "https://myserver.com/webhook",
    "events": ["video.uploaded", "stream.started"]
  }'`}
                                    />
                                </TabsContent>
                            </Tabs>
                        </CardContent>
                    </Card>
                </section>
            </div>
        </DashboardLayout>
    )
}
