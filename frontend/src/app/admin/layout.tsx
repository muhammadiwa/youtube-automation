import { AdminProtectedRoute } from "@/components/admin"

export default function AdminRootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return <AdminProtectedRoute>{children}</AdminProtectedRoute>
}
