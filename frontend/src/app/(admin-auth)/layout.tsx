/**
 * Layout for admin authentication pages (login)
 * This layout does NOT include the AdminProtectedRoute wrapper
 * since these pages need to be accessible before admin authentication
 */
export default function AdminAuthLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return <>{children}</>
}
